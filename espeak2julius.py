import re
import subprocess
import collections
import random
import os, sys
from ID3 import ID3

loglevel = 2

def log(s, level):
    if loglevel>=level:
        print (s)

syllconv = open('julius/espeak-julius.txt').read().splitlines()[1:]

triphones = open ('julius/tiedlist').read()

d = collections.OrderedDict()

# substitutions = {'ix':'iy', 'r': 'er', 'er':'r', 'n':'ng','ey':'ay','aa':'ax','ax':'ae','ih':'ax','eh':'ix','z':'s','jh':'ch','aw':'ow'}
substitutions = {'ix':'iy', 'r': 'er', 'er':'r', 'n':'ng','ey':'ay','aa':'ax','ax':'ae','ih':'ix','eh':'ix','z':'s','jh':'ch','aw':'ow','ey':'ix'}

for i in syllconv:
    splitline = re.split("  +",i)
    if len(splitline)==1: splitline.append('')
    e, j = splitline
    d[e]=j

def e2j(string):
    original_result, err = subprocess.Popen(['espeak','-x','-q',string],stdout=subprocess.PIPE).communicate()
    out = ""
    if sys.version > '3':
        original_result = original_result.decode('utf-8')
    result = original_result.strip()
    while result != "":
        for phoneme in d:
            if result.startswith(phoneme):
                if d[phoneme] != '':
                    out += d[phoneme] + " "
                result = result[len(phoneme):]
                break
        else:
            return "ERROR: Could not translate "+original_result+" - remaining text: "+result
    return out

def create_grammar(stringlist):
    voca = """% NS_B
<s>        sil

% NS_E
</s>        sil

% PLAY
play      p l ey"""
    gram = "S : NS_B PLAY TITLE NS_E\n\n"
    for i, string in enumerate(stringlist):
        words = string.replace('(','').replace(')','').replace('[','').replace(']','').replace('/',' ').replace('-',' ').split()
        c = [e2j(word) for word in words]
        tvoca = ""
        tgram = "\nTITLE:"
        for index, pronunciation in enumerate(c):
            tobreak = False
            tpro = pronunciation.split(' ')
            if len(tpro)>2:
                for k in range(len(tpro)-2):
                    if words[index].lower()=='sorcery': print (tpro)
                    if not "\n"+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2] in triphones:
                        if words[index].lower()=='sorcery': print (tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2]+" not in triphones")
                        if tpro[k] in substitutions and "\n"+substitutions[tpro[k]]+'-'+tpro[k+1]+'+'+tpro[k+2] in triphones:
                            log (words[index]+": substituted "+substitutions[tpro[k]]+" into "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                            tpro[k] = substitutions[tpro[k]]
                            continue
                        elif tpro[k+1] in substitutions and "\n"+tpro[k]+'-'+substitutions[tpro[k+1]]+'+'+tpro[k+2] in triphones:
                            log (words[index]+": substituted "+substitutions[tpro[k+1]]+" into: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                            tpro[k+1] = substitutions[tpro[k+1]]
                            continue
                        elif tpro[k+2] in substitutions and "\n"+tpro[k]+'-'+tpro[k+1]+'+'+substitutions[tpro[k+2]] in triphones:
                            log (words[index]+": substituted "+substitutions[tpro[k+2]]+" into: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                            tpro[k+2] = substitutions[tpro[k+2]]
                            continue
                        print (words[index]+" will fail. Failing triphone: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2])
                        tobreak = True
                        tvoca = ""
                        tgram = ""
                        break
                    else:
                        if words[index].lower()=='sorcery': print (tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2]+" passes")
                if tobreak: break
                # Second pass in case substitutions broke earlier triphones
                for k in range(len(tpro)-2):
                    if not "\n"+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2] in triphones:
                        print (words[index]+" failed second pass. Failing triphone: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2])
                        tobreak = True
                        tvoca = ""
                        tgram = ""
                        break
                pronunciation = ' '.join(tpro)
            if tobreak: break
            tvoca += "\n\n% W_"+str(i)+"_"+str(index)+"\n"+words[index].lower().ljust(10)+' '+pronunciation
            tgram += " W_"+str(i)+"_"+str(index)
        voca += tvoca
        gram += tgram
    voca = voca.replace('ih \n','iy \n').replace(' n k ',' ng k ')
    if not os.path.exists('/tmp/saera'):
        os.mkdir('/tmp/saera')
    open('/tmp/saera/musictitles.grammar','w').write(gram)
    open('/tmp/saera/musictitles.voca','w').write(voca)
    os.system('./julius/ARM/mkdfa.pl /tmp/saera/musictitles')
    return gram, voca

if __name__=="__main__":
    testing = False
    if testing:
        l = open('../dict').read().splitlines()
        m = [(i[:i.index('[')].strip(), i[i.index(']')+1:].strip()) for i in l]
        passed = 0
        failed = 0
        for j in range(100):
            i = random.choice(m)
            result = e2j(i[0])
            if i[1].startswith(result):
                passed +=1
            elif result.startswith("ERROR"):
                print (result)
                break
            else:
                failed += 1
        print ("Passed",passed,", failed",failed)
    lst = []
    files = subprocess.Popen("find /home/nemo/Music/ -type f -name \*.mp3", shell=True, stdout=subprocess.PIPE).communicate()[0].splitlines()#[:30]
    for f in files:
        id3info = ID3(f)
        if id3info.has_tag:
            lst.append(id3info.title)
        else:
            continue
    # print (lst)
    create_grammar(lst)