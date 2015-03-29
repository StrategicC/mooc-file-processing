#!/usr/bin/env python

__author__ = 'Iris'
__project__ = 'processDALMOOC'

import sys
import fileinput
import datetime
from collections import defaultdict
from QHInstance import QuickHelperInstance

# LOGFILE NAMES
FILENAME_HELPERLOG = "helper"
FILENAME_SELECTIONLOG = "selection"
FILENAME_VOTELOG = "vote"
FILENAME_USERLOG = "user"
EXTENSION_LOGFILE = ".log"
EXTENSION_PROCESSED = ".csv"

# IMAGE VARIABLES
BADGE_NONE = "http://erebor.lti.cs.cmu.edu/quickhelper/badges/blank.png"
BADGE_NONE2 = "http://i62.tinypic.com/2mgqut2.jpg"
BADGE_ONE = "http://erebor.lti.cs.cmu.edu/quickhelper/badges/helper1.png"
BADGE_ONE2 = "http://i61.tinypic.com/24q1jyr.jpg"
BADGE_TWO = "http://erebor.lti.cs.cmu.edu/quickhelper/badges/helper2.png"
BADGE_TWO2 = "http://i58.tinypic.com/29yjuww.jpg"
BADGE_THREE = "http://erebor.lti.cs.cmu.edu/quickhelper/badges/helper3.png"
BADGE_THREE2 = "http://i62.tinypic.com/214w7wl.jpg"
BADGE_FOUR = "http://erebor.lti.cs.cmu.edu/quickhelper/badges/helper4.png"
BADGE_FOUR2 = "http://i58.tinypic.com/2cgymgh.jpg"

BADGE_NONE_TXT = "0"
BADGE_ONE_TXT = "1"
BADGE_TWO_TXT = "2"
BADGE_THREE_TXT = "3"
BADGE_FOUR_TXT = "4"

# TEXT-RELATED VARIABLES
CONST_DELIMITERVAR = "<DELIMITER>"
CONST_DELIMITER = ","
CONST_LINESTART = "{\"level\":\"info\",\"message\":\"<DELIMITER>"

# limiting date
CONST_FIRST_DAY = datetime.date(2014, 10, 20)
CONST_LAST_DAY = datetime.date(2014, 12, 17)

# mapping from instance ID to conditions (badge, sentence, voting, userid)
count_repeat = 0
dict_last_digs = {}
dict_helpers = defaultdict(list) # instanceID -> a list of helper IDs shown
dict_selected_helpers = defaultdict(list) # instanceID -> a list of helper IDs that were selected
dict_badge = {}
dict_sentence = {}
dict_voting = {}
dict_user_id = {}

dict_num_helpers = {}
list_all_instances = {}

# TODO: command line input for column delimiters

'''
main function - calls the functions that do the processing for each kind of file
'''
def main():
    # Start the processing of files!
    proc_user()
    proc_selection()
    proc_helper()
    proc_vote()

    file_out = open(FILENAME_USERLOG+EXTENSION_PROCESSED,'w')
    file_out.write(QuickHelperInstance.get_headers(CONST_DELIMITER)+"\n")
    for qh_instance in list_all_instances:
        # set the selected number of helpers for each instance
        setattr(qh_instance, 'num_helpers_selected', dict_num_helpers.get(getattr(qh_instance, 'instance_id'), 0))
        line = qh_instance.to_string(CONST_DELIMITER)
        file_out.write(line+'\n')
    file_out.close()
    print("Done writing " + FILENAME_USERLOG+EXTENSION_LOGFILE)

'''
A line in the Userfile Log represents what user-level variables the user saw (specific information about individual helpers
shown is stored in the Helperfile Log).
ex: {"level":"info","message":"<DELIMITER>100<DELIMITER>1413061797181100<DELIMITER>1<DELIMITER>0<DELIMITER>1<DELIMITER>1<DELIMITER>0<DELIMITER>1833503<DELIMITER>2512601<DELIMITER>1657199<DELIMITER>title1<DELIMITER>body1<DELIMITER>","timestamp":"2014-10-11T21:09:57.182Z"}
Help Seeker User ID, Instance ID, Badge Shown?, Irrelevant Sentence Shown?, Voting Shown?, Anonymized Image Shown?, User ID Shown?, helper0, helper1, helper2, Question title, Question body
'''
def proc_user():
    file_out = open(FILENAME_USERLOG+EXTENSION_PROCESSED,'w')
    file_out.write(QuickHelperInstance.get_headers(CONST_DELIMITER)+"\n")

    with open(FILENAME_USERLOG+EXTENSION_LOGFILE,'r') as f:
        for line in f:
            line = line[len(CONST_LINESTART): len(line)] # Cut off the extra chars from beginning
            line = line.replace(CONST_DELIMITER,' ') # Replace all occurrences of delimiters with empty space
            line = line.replace(CONST_DELIMITERVAR,CONST_DELIMITER) # Replace delimiter stand-in with actual delimiters
            # print(line)
            array_line = line.split(CONST_DELIMITER)
            col_helper_id = array_line[0]
            col_instance_id = array_line[1]
            col_badge_shown = array_line[2]
            col_irrelevant_sentence = array_line[3]
            col_voting = array_line[4]
            col_anon_img = array_line[5]
            col_user_id = array_line[6]
            col_helper0 = array_line[7]
            col_helper1 = array_line[8]
            col_helper2 = array_line[9]
            col_ques_title = array_line[10]
            col_ques_body = array_line[11]
            col_date = get_date(array_line[len(array_line) - 1])  # Due to some wonky extra column with a url
            col_time = get_time(array_line[len(array_line) - 1])
            user_instance = QuickHelperInstance(col_helper_id, col_instance_id, col_badge_shown, col_irrelevant_sentence, col_voting, col_anon_img, col_user_id,col_helper0, col_helper1, col_helper2, col_ques_title, col_ques_body,col_date, col_time)
            line = user_instance.to_string(CONST_DELIMITER)
            list_all_instances.append(user_instance)

            # only write line if it's not a duplicate
            # AND if it's during the right time period
            # AND if it's not one of the researchers' actions
            # AND only if the message body is longer than __ characters.
            # NOTE: add_qh_instance() has to be first in this line, must be called each time!
            if add_qh_instance(col_instance_id,col_badge_shown, col_irrelevant_sentence, col_voting, col_user_id) and is_during_course(col_date) and not is_researcher(col_user_id) and len(col_ques_body)>10:
                file_out.write(line+'\n')

            # Add helper IDs to dictionary of instances to helpers
            dict_helpers[col_instance_id].append(col_helper0)
            dict_helpers[col_instance_id].append(col_helper1)
            dict_helpers[col_instance_id].append(col_helper2)
            #print(line)
    print("Done processing "+FILENAME_USERLOG+EXTENSION_LOGFILE)
    file_out.close()
    print("\tNumber of Repeats: " + str(count_repeat))

'''
A line in the Helperfile Log represents all the information specific to the helper that the user saw.
{"level":"info","message":"<DELIMITER>1<DELIMITER>1413061797181100<DELIMITER>8<DELIMITER>http://i58.tinypic.com/2cgymgh.jpg<DELIMITER>3<DELIMITER>This student has been participating in the course for 1 weeks and the matching of his/her interest and the topic of your query is 100.0 .<DELIMITER>","timestamp":"2014-10-11T21:09:57.182Z"}
'''
def proc_helper():
    file_out = open(FILENAME_HELPERLOG+EXTENSION_PROCESSED,'w')
    file_out.write("HelperUserID"+CONST_DELIMITER+"QuickHelperInstanceID"+CONST_DELIMITER+"HelperUsername"+CONST_DELIMITER+"badgeStarsShown"+CONST_DELIMITER+"NumPrevHelpRequests"+CONST_DELIMITER+"numWeeks"+CONST_DELIMITER+"topicMatch"+CONST_DELIMITER+"recommenderSentence"+CONST_DELIMITER+"date"+CONST_DELIMITER+"time" + CONST_DELIMITER + "wasSelected" + CONST_DELIMITER + "isBadgeCondition" + CONST_DELIMITER + "isIrrelevantSentenceCondition" + CONST_DELIMITER + "isVotingCondition" + CONST_DELIMITER + "isUserIDCondition\n")

    with open(FILENAME_HELPERLOG+EXTENSION_LOGFILE,'r') as f:
        for line in f:
            line = line[len(CONST_LINESTART): len(line)] # Cut off the extra chars from beginning
            line = line.replace(CONST_DELIMITER,' ') # Replace all occurrences of delimiters with empty space
            line = line.replace(CONST_DELIMITERVAR,CONST_DELIMITER) # Replace delimiter stand-in with actual delimiters
            # print(line)
            array_line = line.split(CONST_DELIMITER)
            col_helper_id = array_line[0]
            col_instance_id = array_line[1]
            col_helper_name = array_line[2]
            col_badge_shown = get_badge_stars(array_line[3])
            col4 = array_line[4]
            col_rec_sentence = array_line[5]
            col_num_weeks = get_num_weeks(col_rec_sentence)
            col_topic_match = get_topic_match(col_rec_sentence)
            col_date = get_date(array_line[len(array_line) - 1])  # Due to some wonky extra column with a url
            col_time = get_time(array_line[len(array_line) - 1])
            line = col_helper_id + CONST_DELIMITER + col_instance_id + CONST_DELIMITER + col_helper_name + CONST_DELIMITER + col_badge_shown + CONST_DELIMITER + col4 + CONST_DELIMITER + col_num_weeks + CONST_DELIMITER + col_topic_match + CONST_DELIMITER + col_rec_sentence + CONST_DELIMITER + col_date + CONST_DELIMITER + col_time

            # determine if this helper was selected
            was_selected = 0
            if col_instance_id not in dict_helpers:  # that instance didn't occur in user.log
                was_selected = "null"
                print("WARNING: instanceID in helper.log not found in user.log: " + col_instance_id)
            elif col_helper_id in dict_selected_helpers[col_instance_id]:  # this ID was selected in selection.log
                was_selected = 1
            line += CONST_DELIMITER + str(was_selected)

            # retrieve experimental conditions from dict
            if col_instance_id not in dict_badge:
                print("WARNING: Helper.log instance does not exist in user.log: "+col_instance_id)
            line += CONST_DELIMITER + str(dict_badge.get(col_instance_id,"")) + CONST_DELIMITER + str(dict_sentence.get(col_instance_id,"")) + CONST_DELIMITER + str(dict_voting.get(col_instance_id,"")) + CONST_DELIMITER + str(dict_user_id.get(col_instance_id,""))

            # only write line if it's in our date range
            if is_during_course(col_date):
                file_out.write(line+'\n')
            #print(line)
    print("Done processing "+FILENAME_HELPERLOG+EXTENSION_LOGFILE)
    file_out.close()

'''
A line in the Helperfile Log represents one (of three maximum) of the helpers selected by user
{"level":"info","message":"<DELIMITER>11<DELIMITER>0<DELIMITER>","timestamp":"2014-10-11T21:09:57.211Z"}
'''
def proc_selection():
    file_out = open(FILENAME_SELECTIONLOG+EXTENSION_PROCESSED,'w')
    file_out.write("QuickHelperInstanceID"+CONST_DELIMITER+"HelperSelected"+CONST_DELIMITER+"SelectedHelperID"+CONST_DELIMITER+"date"+CONST_DELIMITER+"time\n")

    with open(FILENAME_SELECTIONLOG+EXTENSION_LOGFILE,'r') as f:
        for line in f:
            line = line[len(CONST_LINESTART): len(line)] # Cut off the extra chars from beginning
            line = line.replace(CONST_DELIMITER,' ') # Replace all occurrences of delimiters with empty space
            line = line.replace(CONST_DELIMITERVAR,CONST_DELIMITER) # Replace delimiter stand-in with actual delimiters
            # print(line)
            array_line = line.split(CONST_DELIMITER)
            col_instance_id = array_line[0]
            col_helper_selected = array_line[1]
            col_date = get_date(array_line[len(array_line) - 1] ) # Due to some wonky extra column with a url
            col_time = get_time(array_line[len(array_line) - 1] )
            line = col_instance_id + CONST_DELIMITER + col_helper_selected + CONST_DELIMITER

            # retrieve helper user ID
            if len(col_helper_selected) > 1: #i.e., it's not 0,1, or 2
                line += ""
            else:
                array_helpers = dict_helpers[col_instance_id] # all helpers shown for this instance
                helper_id = ""
                if len(array_helpers) < int(col_helper_selected)+1: # less helpers than the index of this helper
                    print("WARNING: " + str(len(array_helpers))+" helpers listed for instance " + col_instance_id)
                else: # we have an existing helper
                    helper_id = array_helpers[int(col_helper_selected)]
                line += helper_id

                # record this as a selected helper for helper.log
                dict_selected_helpers[col_instance_id].append(helper_id)
                dict_num_helpers[col_instance_id] = int(dict_num_helpers.get(col_instance_id, 0)) + 1 # add one to our number of helpers selected

            # continue...
            line += CONST_DELIMITER + col_date + CONST_DELIMITER + col_time

            # only write line if it's in our date range
            if is_during_course(col_date):
                file_out.write(line+'\n')
            #print(line)
    print("Done processing "+FILENAME_SELECTIONLOG+EXTENSION_LOGFILE)
    file_out.close()

'''
A line in the Upvote Log represents each instance a Helper up or downvotes a QuickHelp request.
{"level":"info","message":"<DELIMITER>2231948<DELIMITER>1<DELIMITER>1<DELIMITER>","timestamp":"2014-10-11T06:05:13.668Z"}
'''
def proc_vote():
    file_out = open(FILENAME_VOTELOG+EXTENSION_PROCESSED,'w')
    file_out.write("HelperUserID"+CONST_DELIMITER+"QuickHelperInstanceID"+CONST_DELIMITER+"Vote"+CONST_DELIMITER+"date"+CONST_DELIMITER+"time\n")

    with open(FILENAME_VOTELOG+EXTENSION_LOGFILE,'r') as f:
        for line in f:
            line = line[len(CONST_LINESTART): len(line)] # Cut off the extra chars from beginning
            line = line.replace(CONST_DELIMITER,' ') # Replace all occurrences of delimiters with empty space
            line = line.replace(CONST_DELIMITERVAR,CONST_DELIMITER) # Replace delimiter stand-in with actual delimiters
            # print(line)
            array_line = line.split(CONST_DELIMITER)
            col_helper_id = array_line[0]
            col_instance_id = array_line[1]
            colVote = array_line[2]
            col_date = get_date(array_line[len(array_line) - 1] ) # Due to some wonky extra column with a url
            col_time = get_time(array_line[len(array_line) - 1] )
            line = col_helper_id + CONST_DELIMITER + col_instance_id + CONST_DELIMITER + colVote + CONST_DELIMITER + col_date + CONST_DELIMITER + col_time

            # only write line if it's in our date range
            if is_during_course(col_date):
                file_out.write(line+'\n')
            #print(line)
    print("Done processing "+FILENAME_VOTELOG+EXTENSION_LOGFILE)
    file_out.close()

'''
 Adds a QuickHelper instance (and conditions) to our condition dictionaries
only if it's not already in the dictionaries (last __ digits tend to be the same in duplicates)
'''
def add_qh_instance(instance_id, condBadge, condSentence, condVoting, condUser):
    # put last 7 digits of instanceID in dictLast7digs
    last_digs = instance_id[-7:]
    make_new_instance = dict_last_digs.get(last_digs,"dne") # return 0 if it doesn't exist

    # all duplicates get added to our condition dictionaries
    # since helper.log needs it (i.e., the first entry isn't
    # always the one that was shown!
    dict_badge[instance_id] = condBadge
    dict_sentence[instance_id] = condSentence
    dict_voting[instance_id] = condVoting
    dict_user_id[instance_id] = condUser

    if make_new_instance != "dne": # item already exists, is a duplicate
        dict_last_digs[last_digs] = "duplicate";
        global count_repeat
        count_repeat+= 1
        return False
    else: # item does not exist, add it
        dict_last_digs[last_digs] = "exists";
        return True

'''
Determine if given date is within the range of dates the course took place
'''
def is_during_course(instance_date):
    if len(instance_date) == 10:
        array_date = instance_date.split("-")
        date_converted = datetime.date(int(array_date[0]), int(array_date[1]), int(array_date[2]))
        if date_converted >= CONST_FIRST_DAY and date_converted <= CONST_LAST_DAY :
            return True
        else: # Not in given course date range
            return False
    else:
        print("ERROR processing date column: " + instance_date)
        return False
'''
Determine if given user is one of the researchers
TODO: Not sure if this works for the user.log file?
'''
def is_researcher(userID):
    # 5542424 - ryansbaker
    # 5556926 - diyi
    # 5529557 - ferschke
    # 2030452 - dgasevic
    # 4480312 - sreckojoksimovic
    # 2805898 - UTAMatt
    list_researchers = {5542424, 5556926, 5529557, 2030452, 4480312, 2805898}

    if int(userID) < 0 or int(userID) in list_researchers: # TAs and researchers had userIDs less than 0
        return True
    else: # Not a researcher!
        return False

'''
Gets the date from a messy timestamp in the logfiles
'''
def get_date(tstamp):
    tstamp = tstamp[tstamp.index(':')+1: (len(tstamp)-2)].replace("\"",'')
    return tstamp[0:tstamp.find("T")]

'''
Gets the time from a messy timestamp in the logfiles
'''
def get_time(tstamp):
    tstamp = tstamp[tstamp.index(':')+1: (len(tstamp)-2)].replace("\"",'')
    return tstamp[tstamp.find("T")+1: len(tstamp)-1]

'''
Determines how many stars were on the badge, depending on badge URL
'''
def get_badge_stars(url):
    if url == BADGE_NONE or url == BADGE_NONE2:
        return BADGE_NONE_TXT
    elif url == BADGE_ONE or url == BADGE_ONE2:
        return BADGE_ONE_TXT
    elif url == BADGE_TWO or url == BADGE_TWO2:
        return BADGE_TWO_TXT
    elif url == BADGE_THREE or url == BADGE_THREE2:
        return BADGE_THREE_TXT
    elif url == BADGE_FOUR or url == BADGE_FOUR2:
        return BADGE_FOUR_TXT
    else:
        print("ERROR: Missing badge ID: " + url)

'''
Finds what the topic match percentage was given the topic match sentence
'''
def get_topic_match(sentence):
    if sentence.find("Teaching Assistants") >= 0:
        return "TA"
    else:
        tm = sentence[len(sentence)-7:len(sentence)-1]
        tm = float(tm.strip("abcdefghijklmnopqrstuvwxyz% "))
        if tm < 1:
            tm = tm*100
        return str(tm)

'''
Finds how many weeks the helper's been around, given the topic match sentence
'''
def get_num_weeks(sentence):
    if sentence.find("Teaching Assistants") >= 0:
        return "TA"
    else:
        return sentence[sentence.find("week")-2: sentence.find("week")]

'''
Calls the main function, not the smoothest thing to do.
'''
main()