#!/usr/bin/python3

import openai
import speech_recognition as sr
import re
from colorama import Fore, Back, Style
import gtts  
from io import BytesIO
#import string
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
from pygame import mixer
from time import sleep
from fuzzywuzzy import fuzz, process
import warnings
warnings.filterwarnings("ignore")


def split_by_actual_punctuation(input_str):
    # Define the regular expression for splitting around double quotes
    quote_regex = r'("[^"]*")'

    # Split the input string around double quotes
    split_str = re.split(quote_regex, input_str)

    # Initialize the list of split sections
    split_list = []

    # Loop over each split section
    for section in split_str:
        # If the section is enclosed in double quotes, add it to the split list as is
        if section.startswith('"') and section.endswith('"'):
            split_list.append(section)
        else:
            # Define the regular expression for splitting the section by actual punctuation marks
            regex = r'(?:[^\'".,!?;:\s]+|\S+(?<!\s))[\.,!?;:]+(?=\s+|$|\W)'

            # Find all non-overlapping matches of the regular expression in the section
            matches = re.findall(regex, section)

            # Extract the corresponding substrings from the section
            start_index = 0
            for match in matches:
                match_obj = re.search(re.escape(match), section[start_index:])
                end_index = start_index + match_obj.end()
                split_list.append(section[start_index:end_index].strip())
                start_index = end_index

            # Add any remaining text to the list
            if start_index < len(section):
                split_list.append(section[start_index:].strip())
    
    joined_list = []
    i = 0
    while i < len(split_list):
        # if (split_list[i].endswith(",") or split_list[i].endswith(":")) and i + 1 < len(split_list):
        if split_list[i].endswith(",") and i + 1 < len(split_list):
            combined_string = split_list[i] + " " + split_list[i+1]
            if len(combined_string) <= 100:
                joined_list.append(combined_string)
                i += 2
            else:
                joined_list.append(split_list[i][:-1])
                joined_list.append(split_list[i+1])
                i += 2
        else:
            joined_list.append(split_list[i])
            i += 1
    return joined_list
    
def syntax_highlighting(text):
    # Split the string by triple backticks
    split_string = re.split(r'```', text)

    # Wrap all even items in ANSI color codes for a grey background
    for i in range(len(split_string)):
        if i % 2 == 0:
        
            # Regular expression to match text within double quotes
            quotes_regex = re.compile(r'"([^"]*)"')
            split_string[i] = quotes_regex.sub(
                lambda match: f"\033[48;2;191;191;191m\033[30m\"{match.group(1)}\"\033[0m",
                split_string[i]
            )

        else:
            split_string[i] = re.sub(r'^\w*\s?', '', split_string[i])
            split_string[i] = '\033[48;2;191;191;191m\033[30m' + split_string[i] + '\033[0m'

    # Join the string back together
    output_string = ''.join(split_string)
    
       # Highlight text between backticks in all sections
    backticks_regex = re.compile(r'`([^`]*)`')
    output_string = backticks_regex.sub(
        lambda match: f"{Fore.BLUE}{Style.BRIGHT}`{match.group(1)}`{Style.RESET_ALL}",
        output_string
    )

    # Return the output string
    return output_string

def skip_over_code(text):
    sections = text.split('```')
    even_sections = [sections[i] for i in range(len(sections)) if i % 2 == 0]
    return ' '.join(even_sections)
    
def gtts_speak(wordz):
    mixer.init()
    mp3_fp = BytesIO()
    tts = gtts.gTTS(wordz, lang='en', tld='com')
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    mixer.music.load(mp3_fp, "mp3")
    channel = mixer.music.play()
    try:
        while mixer.music.get_busy():
            continue
    except KeyboardInterrupt:
        mixer.music.stop()
        return

def get_audio_input(prompt):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        if prompt:
            print()
            print('*'*40,"\nSpeak now...")
        audio = recognizer.listen(source)
    try:
        user_input = recognizer.recognize_google(audio)
        print("\nParsed Input:", user_input)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return None

        
    return user_input
    
def query_chatgpt(message_context):
   
    response=openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=message_context
    )
    
    #grab response object
    response_object=response.choices[0].message
    
    #append reponse object to context
    #message_context.append(response_object)
    
    # Get the chatbot's response
    chatbot_response = response_object.content
   
    return chatbot_response
       
def speak_and_print(content):
    #print the message out
    print("\nBot:", syntax_highlighting(content))
    
    #debug
    #print(split_by_actual_punctuation(content))

    if content:
        #doesn't tyr to sade the codey bits
        verbal_response = skip_over_code(content)
        #print('\n'*2,split_by_actual_punctuation(verbal_response),'\n'*2,)
        try:
            # Define a regex pattern to remove unwanted characters from the chatbot's response
            pattern = re.compile("[^\w\s]")
            #split it on actual punctuation and not things with comments and stuff
            for sentence_chunk in split_by_actual_punctuation(verbal_response):
                sentence_chunk=sentence_chunk.strip('"')
                if sentence_chunk:
                    gtts_speak(re.sub(pattern, "", sentence_chunk))

        except KeyboardInterrupt:
            return

def check_operator(string):
    return string.lower().startswith('operator')
     
def check_operator_command(string):
    commands = ['text input', 'holdup', 'go to sleep', 'switch to text mode ', 'switch to text input','save to file', 'quit', 'exit program']
    #remove the word operator
    command = re.sub(r'(?i)operator\s*', '', string)
    best_match = process.extractOne(command, commands, scorer=fuzz.token_sort_ratio)
    if best_match[1] >= 80:
        return best_match[0]
    else:
        return False
      
def get_multiline_input():
    """
    Reads user input until a line containing only the letter 'z' is entered,
    then returns the input as a string.
    """
    print("Please enter your input below (use 'z' on a new line to end input):")

    # Initialize an empty input string
    multi_input = ""

    while True:
        # Read input from the user
        line = input().strip()

        if line == "z":
            # If the user enters a line consisting entirely of 'z's, break the loop
            break
        else:
            # Otherwise, append the input to the input string
            multi_input += line + "\n"

    return multi_input

def auth_to_openai():
    # Path to the API key file
    api_key_file = os.path.expanduser("~/.openai/api_key.txt")
    # Check if the API key file exists
    if os.path.isfile(api_key_file):
        with open(api_key_file, "r") as file:
            api_key = file.read().strip()
    else:
        # Prompt the user to enter an API key
        api_key = input("You have no API key set. Please enter your OpenAI API key: ").strip()

        # Create the directory if it doesn't exist
        directory = os.path.dirname(api_key_file)
        os.makedirs(directory, exist_ok=True)

        # Write the API key to the file
        with open(api_key_file, "w") as file:
            file.write(api_key)

    # Set the API key
    openai.api_key = api_key
    
		
def do_the_thing():
	auth_to_openai()    
		
	# Create a new SpeechRecognition recognizer
	recognizer = sr.Recognizer()

	purpose = "The following is a conversation between a user and a chatbot. The user is trying to have a conversation with the chatbot."

	# Define the initial message
	initial_message = "Hello Brandon, how can I help you today?"

	print("Bot: "+initial_message)

	gtts_speak(initial_message)

	message_context=[
		{"role": "system", "content": purpose},
		{"role": "assistant", "content": initial_message},
	]

	def operator(command):
		
		if best_match[1] >= 80:
		    speak_and_print(f"your command is {best_match[0]}")
		else:
		    speak_and_print(f"`{command}` does not match any operator commands ")
		
		
	prompt_for_talk=True
	'''
	while True:
		user_input = get_audio_input(prompt_for_talk)
		#print(message_context)
		if user_input is not None:
		    if check_operator(user_input):
		        possible_command=re.sub(r'(?i)operator\s*', '', user_input)
		        yep_a_command=check_operator_command(possible_command)
		        if yep_a_command:
		            if "switch to text" in yep_a_command:
		                user_input=get_multiline_input()
		            if "quit" in yep_a_command:
		                exit()
		            if "holdup" in yep_a_command or "sleep" in yep_a_command:
		                input("\nHit any key to continue")
		                prompt_for_talk=True
		                continue
		            else:
		                speak_and_print(f"running command: {yep_a_command}")
		                prompt_for_talk=True
		                continue
		        else:
		            
		            speak_and_print(f"`{yep_a_command}` does not match any operator commands ")
		            prompt_for_talk=True
		            continue
		        

		    message_context.append({"role": "user", "content": user_input})
		    
		    chatbot_response=query_chatgpt(message_context) 
		    #chatbot_response="chatbot response "+user_input
		    
		    if chatbot_response:
		    
		        message_context.append({"role": "assistant", "content": chatbot_response})
		        
		        speak_and_print(chatbot_response)
		    else:
		        speak_and_print("no response")
		    
		    prompt_for_talk=True
		else:
		    prompt_for_talk=False
	'''
	while True:
		user_input = get_audio_input(prompt_for_talk)
		#print(message_context)
		if user_input is not None:
		    if check_operator(user_input):
		        possible_command=re.sub(r'(?i)operator\s*', '', user_input)
		        yep_a_command=check_operator_command(possible_command)
		        print(yep_a_command)
		        if yep_a_command:
		            if "text input" in yep_a_command:
		                user_input=get_multiline_input()
		                prompt_for_talk=True
		            elif "quit" in yep_a_command:
		                exit()
		            elif "holdup" in yep_a_command or "sleep" in yep_a_command:
		                input("\nHit any key to continue")
		                prompt_for_talk=True
		                continue
		            else:
		                speak_and_print(f"not running command: {yep_a_command}")
		                prompt_for_talk=True
		                continue
		        else:
		            
		            speak_and_print(f"`{yep_a_command}` does not match any operator commands ")
		            prompt_for_talk=True
		            continue
		            
		            
		    message_context.append({"role": "user", "content": user_input})
		    
		    chatbot_response=query_chatgpt(message_context) 
		    #chatbot_response="chatbot response "+user_input
		    
		    if chatbot_response:
		    
		        message_context.append({"role": "assistant", "content": chatbot_response})
		        
		        speak_and_print(chatbot_response)
		    else:
		        speak_and_print("no response")
		    
		    prompt_for_talk=True
		else:
		    prompt_for_talk=False
		    
if __name__ == "__main__":
    do_the_thing()
