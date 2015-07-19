import re
import subprocess
try:
    from collections import OrderedDict
except ImportError: # for python2.6 and lower
    from ordereddict import OrderedDict
import random
import os, sys
from ID3 import ID3

loglevel = 1

def log(s, level):
    if loglevel>=level:
        print (s)

f = __file__.split('espeak2julius.py')[0]

syllconv = open(f+'julius/espeak-julius.txt').read().splitlines()[1:]

triphones = open (f+'julius/tiedlist').read().split()

d = OrderedDict()

jd = open (f+'julius/dict').read().splitlines()
jdict = dict([(i.split('[')[0].strip(), i.split(']')[-1].replace('sp','').strip()) for i in jd])

# substitutions = {'ix':'iy', 'r': 'er', 'er':'r', 'n':'ng','ey':'ay','aa':'ax','ax':'ae','ih':'ax','eh':'ix','z':'s','jh':'ch','aw':'ow'}
substitutions = {'ix':'iy', 'iy':'ix', 'r': 'er', 'er':'r', 'n':'ng','ey':'ay','ay':'ey','aa':'ax','ax':'ae', 'ae':'ax','ih':'ix','eh':'ix', 'ah':'ax','z':'s','jh':'ch','aw':'ow','ey':'ix', 'uw':'ow', 'dh':'th'}

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
    return out.strip()

def create_grammar(stringlist, gramname, gramtype):
    if gramtype=='songtitles':
        voca = """% NS_B
<s>        sil

% NS_E
</s>        sil

% PLAY
play      p l ey"""
        gram = "S : NS_B PLAY TITLE NS_E\n\n"
    elif gramtype=='contacts':
        voca = """% NS_B
<s>        sil

% NS_E
</s>        sil

% CALL
call       k ao l

% TEXT
text       t eh k s t
"""
        gram = "S : NS_B CALL NAME NS_E\nS : NS_B CALL FIRSTNAME NS_E\nS : NS_B TEXT NAME NS_E\nS : NS_B TEXT FIRSTNAME NS_E\n\n"
    elif gramtype=='addresses':
        voca = """% NS_B
<s>        sil

% NS_E
</s>       sil

% DIRECTIONS
directions d er eh k sh ax n s

% TO
to         t uw

% DIGIT
five       f ay v
four       f ao r
nine       n ay n
eight      ey t
oh         ow
one        w ah n
seven      s eh v ax n
six        s ih k s
three      th r iy
two        t uw
zero       z ih r ow
"""
        gram = "S : NS_B DIRECTIONS TO ADDRESS NS_E\nNUMBER: DIGIT\nNUMBER: NUMBER DIGIT\nADDRESS: NUMBER STREET_STRUCT\n\n"
        streettypes = {"ln":("lane","l ey n"),
                       "rd":("road","r ow d"),
                       "way":("way","w ey"),
                       "pl":("place","p l ey s"),
                       "plz":("plaza","p l aa z ax"),
                       "hwy":("highway","hh ax w ey"),
                       "dr":("drive","d r ay v"),
                       "pike":("pike","p ay k"),
                       "expy":("expressway","ix k s p r eh s w ey"),
                       "sq":("square","s k w eh r"),
                       "tpke":("turnpike","t uh r n p ay k"),
                       "drive":("drive","d r ay v"),
                       "st":("street","s t r iy t"),
                       "cir":("circle","s er k ax l"),
                       "fwy":("freeway","f r iy w ey"),
                       "trce":("terrace","t eh r ax s"),
                       "road":("road","r ow d"),
                       "pky":("parkway","p aa k w ey"),
                       "walk":("walk","w ao k"),
                       "blvd":("boulevard","b uh l ix f aa r d"),
                       "aly":("alley","ae l iy"),
                       "ave":("avenue","ae v ax n uw"),
                       "ter":("terrace","t eh r ax s"),
                       "ct":("court","k ao r t"),
                       "row":("row","r ow")}
        used_streettypes = []
    for i, string in enumerate(stringlist):
        pvoca = ""
        pgram = ""
        if gramtype=='addresses':
            string, streettype = string
            if not streettype in streettypes:
                continue
            if not streettype in used_streettypes:
                v = gram.splitlines()
                if v[-1].startswith("STREET_STRUCT:"):
                    v = v[:-1]
                    gram = '\n'.join(v)+'\n'
                    n = voca.splitlines()
                    n = n[:-2]
                    voca = '\n'.join(n)+'\n'
                used_streettypes.append(streettype)
                gram += "\nSTREET_STRUCT: "+streettype.upper()+"_NAME_STRUCT "+streettype.upper()+"\n"
                voca += "\n% "+streettype.upper()+"\n"+streettypes[streettype][0]+"   "+streettypes[streettype][1] #+"\n\n%"+streettype.upper()+"_NAME\n"
                print (streettype)
            else:
                pgram_base = ""
                pvoca_base = ""
        words = string.replace('(','').replace(')','').replace('[','').replace(']','').replace('/',' ').replace('-',' ').strip().split()
        c = []
        for word in words:
            if word.upper() in jdict:
                print ("Found "+word.upper()+" in dict")
                c.append(jdict[word.upper()])
            else:
                c.append(e2j(word))
        # c = [e2j(word) for word in words]
        tvoca = ""
        if gramtype=="songtitles":
            tgram = "\nTITLE:"
        elif gramtype=="contacts":
            tgram = "\nFIRSTNAME:"
        elif gramtype=="addresses":
            tgram = "\n"+streettype.upper()+"_NAME_STRUCT:"
        for index, pronunciation in enumerate(c):
            tobreak = False
            tpro = pronunciation.split(' ')
            if len(tpro)>2:
                for k in range(len(tpro)-2):
                    if words[index].lower()=='concord': print (tpro)
                    if not tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2] in triphones:
                        if words[index].lower()=='concord':print (1)
                        if tpro[k] in substitutions and substitutions[tpro[k]]+'-'+tpro[k+1]+'+'+tpro[k+2] in triphones:
                            if words[index].lower()=='concord': print (2)
                            log (words[index]+": substituted "+substitutions[tpro[k]]+" into "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                            tpro[k] = substitutions[tpro[k]]
                            continue
                        elif tpro[k+1] in substitutions and tpro[k]+'-'+substitutions[tpro[k+1]]+'+'+tpro[k+2] in triphones:
                            if words[index].lower()=='concord': print (3)
                            log (words[index]+": substituted "+substitutions[tpro[k+1]]+" into: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                            tpro[k+1] = substitutions[tpro[k+1]]
                            continue
                        elif tpro[k+2] in substitutions and tpro[k]+'-'+tpro[k+1]+'+'+substitutions[tpro[k+2]] in triphones:
                            if words[index].lower()=='concord': print (4)
                            log (words[index]+": substituted "+substitutions[tpro[k+2]]+" into: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                            tpro[k+2] = substitutions[tpro[k+2]]
                            continue
                        log (words[index]+" will fail. Failing triphone: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                        tobreak = True
                        tvoca = ""
                        tgram = ""
                        break
                    else:
                        if words[index].lower()=='concord': print (tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2]+" passes")
                if tobreak: break
                # Second pass in case substitutions broke earlier triphones
                for k in range(len(tpro)-2):
                    if not tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2] in triphones:
                        log (words[index]+" failed second pass. Failing triphone: "+tpro[k]+'-'+tpro[k+1]+'+'+tpro[k+2], 2)
                        tobreak = True
                        tvoca = ""
                        tgram = ""
                        break
                pronunciation = ' '.join(tpro)
                if words[index].lower()=='concord': print (pronunciation)
            if tobreak: break
            w = words[index].capitalize() if gramtype=="contacts" else words[index].lower()
            tvoca += "\n\n% W_"+str(i)+"_"+str(index)+"\n"+w.ljust(10)+' '+pronunciation
            if words[index].lower()=='concord': print (tvoca)

            tgram += " W_"+str(i)+"_"+str(index)
            if index==0 and len(c)>1:
                voca += tvoca
                gram += tgram
                tvoca = ""
                if gramtype=="contacts":
                    tgram = "\nNAME: W_"+str(i)+"_"+str(index)
        voca += tvoca
        gram += tgram
        newgram = []
        for line in gram.splitlines():
            if not line=="TITLE:":
                newgram.append(line)
        gram = '\n'.join(newgram)
    # voca = voca.replace('ih \n','iy \n').replace(' n k ',' ng k ')
    home = os.getenv('HOME')
    if not os.path.exists(home+'/.cache/saera'):
        os.mkdir(home+'/.cache/saera')
    open(home+'/.cache/saera/'+gramname+'.grammar','w').write(gram)
    open(home+'/.cache/saera/'+gramname+'.voca','w').write(voca)
    # try:
    os.system('perl '+f+'julius/ARM/mkdfa.pl '+home+'/.cache/saera/'+gramname)
    # except
    print (f+'julius/ARM/mkdfa.pl '+home+'/.cache/saera/'+gramname)
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
