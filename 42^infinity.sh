# Choose your language here, only English is supported yet  
# (html structure of answers from *.answers.com are different)
lang="en"
if [ "${lang}" = 'en' ]; then 
   lang_flag='wiki'
else 
   lang_flag=${lang}
fi

# Maximum speech recording time in sec
speech_rec_time=4  					#use for arecord
speech_num_buffers="$(( 50 * ${speech_rec_time} ))"  	#used for gstreamer 

# Default sample rate for flac. Use 48000 if you are using arecord + flac 
# as flac's --sample-rate=16000 does not work for me  
sample_rate=16000

# Just a shortcut for Google's Voice API Url
api_url='http://www.google.com/speech-api/v1/recognize?lang=${lang}-${lang}&client=chromium'

# Temporary files are named as below with the corresponding suffix
file_prefix='file_temp'
rm -f ${file_prefix}* 


# Record voice via gstreamer tool gst-launch, alternatively you can use arecord and flac
record_voice()
{
    gst-launch-0.10 pulsesrc num-buffers=${speech_num_buffers} ! audioconvert !  audioresample \
         ! audiorate ! audio/x-raw-int,rate=${sample_rate} ! flacenc ! filesink location=${file_prefix}.flac \
         1>/dev/null 2>&1

    #arecord -f dat -d ${speech_rec_time} ${file_prefix}.wav 1>/dev/null 2>&1
    #flac --compression-level-5 ${file_prefix}.wav 1>/dev/null 2>&1
    #Remark: sox on N900 doesnt work as below i.e. has no flac support and is not available on N9 
    #sox ${file_prefix}.wav ${file_prefix}.flac rate 16k gain -n -5 silence 1 5 2%
}


# Speech2Txt uses Google Voce API
speech2txt()
{
    wget -q -U "Mozilla/5.0" --post-file ${file_prefix}.flac \
     --header="Content-Type: audio/x-flac; rate=${sample_rate}" -O \
     - ${api_url} > ${file_prefix}.ret
    cat ${file_prefix}.ret | sed 's/.*utterance":"//' | sed 's/","confidence.*//' > ${file_prefix}.txt
}


# Sanity check if something went wrong, i.e. we have no resp. wrong answer from answers.com
error_handling()
{
    errorcheck=`cat ${file_prefix}.txt | cut -c1-4`
    if [ "${errorcheck}" = "http" -o "${errorcheck}" = "" ]; then
       echo 'Sorry, i did not get your question.' > ${file_prefix}.txt
    fi
}


# Get answer from answers.com
get_answer()
{
    # For our question we are repacing ' ' by '_' as a typical request is handled in the http header 
    # for instance http://wiki.answers.com/Q/who_is_michael_jordan
    sed -e 's/ /_/g' ${file_prefix}.txt > ${file_prefix}2.txt

    request_url="http://${lang_flag}.answers.com/Q/"`cat ${file_prefix}2.txt`
    wget ${request_url} --output-document=${file_prefix}.html 1>/dev/null 2>&1
   
    # The first occurance of 'description' contains our answer
    grep 'description' ${file_prefix}.html | head -1 | cut -d"\"" -f4,4 > ${file_prefix}.txt
}


# Txt2speech uses espeak
txt2speech()
{
    espeak -v${lang} -f ${file_prefix}.txt 1>/dev/null 2>&1
}


# Cleanup of temporary files
cleanup()
{
    rm -f ${file_prefix}* 
}

while true; 
do 	
    echo
    printf 'Recording sound input.................'
    record_voice
    echo

    printf 'Speech2txt via Google Voice...........'
    speech2txt; cat ${file_prefix}.txt

    printf 'Getting answer from answers.com.......'   
    get_answer
    error_handling 
    cat ${file_prefix}.txt

    printf 'Txt2speech via espeak.................' 
    txt2speech
    echo
   
    cleanup
done
