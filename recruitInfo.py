import os
import smtplib
import time
from pathlib import *
from tkinter import OptionMenu,StringVar,Label,Entry,Button,Tk
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup

'''
Known Bugs:
- If two or more players have the same name it will update the records.txt for the first persons name with the second/third/fourth etc persons rating.
    + Add HighSchool field to records.txt and that is passed to functions.

Things to add:
- Multi-threading
    + 1) One thread for the GUI.
    + 2) One thread for the terminal that can run in the background.
- Send one big message
    + append each text message to a new line on a string. send it out as one message
- Recipients list
    + for each team have recipients.txt with a phone number and carrier for each person signed up. loop through and send the message.
- Recieve ratings changes / interest changes notification buttons
    +
- Only send text notifications if interest is equal to warm, warmer, favorite.
    +
'''

teams = []
phoneProviders = ["Verizon","AT&T","T-Mobile","Sprint"]

def getSchoolCommitedTo(link):
    location = link.find("title=")
    substring = link[location+7:]
    temp = substring.find('"')
    return substring[0:temp]

def grabD1Teams():
    url = "https://247sports.com/Season/2021-Football/CompositeTeamRankings/"
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"}

    req = Request(url,headers=header)
    page = urlopen(req).read()
    page_soup = soup(page,"html.parser")

    team = page_soup.findAll('a','rankings-page__name-link')

    for each in team:
        teams.append(each.text)

def createWindow():
    startform = Tk()
    startform.title = "Recruit Notifications"
    
    startform.geometry("800x600")
    startform.resizable(1000,1000)

    # Sort the arrays in alphabetical order.
    teams.sort()
    phoneProviders.sort()
    
    selectedTeam = StringVar() # Tkinter variable to hold the current selection
    dropDown = OptionMenu(startform, selectedTeam, *teams)
    dropDown.grid(row = 0, column = 1)

    phoneCarrier = StringVar()
    phoneDrop = OptionMenu(startform,phoneCarrier,*phoneProviders)
    phoneDrop.grid(row = 1, column = 1)

    teamSelectLabel = Label(startform, text = "Please select a team.")
    phoneProviderLabel = Label(startform, text = "Please select a phone provider")
    phoneNumberEntry = Entry(startform)
    
    teamSelectLabel.grid(row = 0)
    phoneProviderLabel.grid(row = 1)

    phoneNumberLabel = Label(startform,text= "Please enter your phone number (no spaces,dashes etc.)")
    phoneNumberEntry.grid(row = 2, column = 1)
    phoneNumberLabel.grid(row = 2)

    submitButton = Button(startform,text="Submit", command = lambda: getSchoolRecruitInfo(phoneCarrier.get(),phoneNumberEntry.get(),selectedTeam.get())) #lambda functions allow it to be done on button click each time
    submitButton.grid(row = 3)

    startform.mainloop()

def makeRecordsFile(team, name, position, interest, starRating):

    paramaters = locals()

    athInfo = str(name)
    athInfo = athInfo.split(' ')
    fullName = athInfo[1] + ' ' + athInfo[2]
    
    pos = paramaters.get("position")
    pos = pos.strip()

    if starRating == 'NA':
        starRating = 0.0000

    currentDir = os.path.dirname(__file__)
    dirName = currentDir + '/my/' + team + "/"
    Path(dirName).mkdir(parents=True,exist_ok=True) # Makes a directory for each team. If it exists doesnt do anything.

    filePath = os.path.join(dirName,"records.txt") # places records.txt in the directory we made.

    file = open(filePath,"a")
    file.write(fullName + "," + pos + "," + interest + "," + str(starRating) + '\n')
    file.close()

def sendTextAlert(name, starRating, prevRating, phoneCarrier, phoneNumber, team, interest, reason):
    param = locals()
    
    sendMSG = smtplib.SMTP("smtp.gmail.com", 587)
    sendMSG.ehlo()
    sendMSG.starttls()
    sendMSG.login("oconnornoah44@gmail.com","vvjidpgxiqxahjwf")

    difference = (float(param.get("starRating")) - float(param.get("prevRating")))
    
    strDifference = '{:.4f}'.format(difference)

    if float(strDifference) > 0.0000:
        message = param.get("name") + "'s rating has changed. They are now " + str(param.get("starRating")) + " (+" + strDifference + ")"
    else:
        message = param.get("name") + "'s rating has changed. They are now " + str(param.get("starRating")) + " (" + strDifference + ")"

    extension = ""

    school = str(param.get('team'))
    schoolList = list(school)
    schoolList[0] = schoolList[0].upper()
    schoolCapitalized = ''.join(schoolList) # joins empty list to schoolList

    if str(param.get('phoneCarrier')) == "Verizon":
        extension = "@vzwpix.com"
    elif str(param.get('phoneCarrier')) == "AT&T":
        extension = "@mms.att.net"
    elif str(param.get('phoneCarrier'))  == "Sprint":
        extension = "@pm.sprint.com"
    else:
        extension = "@tmomail.net"

    recipient = str(param.get('phoneNumber'))+extension

    if reason == 'rating':
        sendMSG.sendmail('oconnornoah44@gmail.com',recipient,message)
    else:
        # They commited to a school.
        if str(param.get('interest') != 'Warm' and str(param.get('interest')) != 'Cool' and str(param.get('interest')) != 'Favorite' and str(param.get('interest')) != 'None' and str(param.get('interest') != 'Warmer')):
            message = str(param.get("name")) + "'s interest in " + schoolCapitalized + " has changed. They are now commited to " + str(param.get('interest')) + '.'
        else:
            message = str(param.get("name")) + "'s interest in " + schoolCapitalized + " has changed. They now have " + str(param.get('interest')) + ' status interest.'
        sendMSG.sendmail('oconnornoah44@gmail.com',recipient,message)
    sendMSG.quit()

def checkRankings(team,name,position,interest,starRating, phoneCarrier, phoneNumber):
    
    args = locals()
    
    currentDir = os.path.dirname(__file__)
    filePath = currentDir + '/my/' + team + "/records.txt"
    
    file = open(filePath, 'r')
    lines = file.readlines()

    lengthLines = len(lines)

    if(starRating == 'NA'):
        starRating = 0.0000 #unranked
    else:
        i = 0
        for line in lines:
            
            text = str(line)
            commaLoc = line.find(',')
            fullName = line[0:commaLoc]

            text = text[commaLoc+1:]

            commaLoc = text.find(',')
            pos = text[0:commaLoc]
            text = text[commaLoc+1:]

            commaLoc = text.find(',')
            status = text[0:commaLoc]
            text = text[commaLoc+1:]

            rating = text

            passedRating = float(args.get("starRating"))
            passedInterest = (args.get('interest'))

            if((args.get("name") == fullName) and (passedRating != float(rating))):
                #found = True
                print("Names match but ratings differ sending a text")
                print("Passed rating = " + str(passedRating) + ". Rating on file = " + str(rating))
                sendTextAlert(fullName, str(passedRating), str(rating), args.get('phoneCarrier'), args.get('phoneNumber'),args.get('team'),interest,'rating')
                # update records file.
                temp = str(name) + "," + str(args.get('position')).strip() + ',' + str(args.get('interest')) + ',' + str(passedRating)
                lines[i] = temp + '\n'
                out = open(filePath,'w')
                out.writelines(lines)
                out.close()
                break
            elif((args.get("name") == fullName) and (status != str(passedInterest))):
                #found = True
                print("Names match but team interest differ sending a text")
                print("Passed status = " + str(passedInterest) + ". Status on file = " + str(status))
                sendTextAlert(fullName, str(passedRating), str(rating), args.get('phoneCarrier'), args.get('phoneNumber'),args.get('team'),interest,'interest')

                # update records file.
                temp = str(name) + "," + str(args.get('position')).strip() + ',' + str(args.get('interest')).strip() + ',' + str(passedRating).strip()
                print("Updating file with: \n" + temp + '\n')
                lines[i] = temp + '\n'
                out = open(filePath,'w')
                out.writelines(lines)
                out.close()
                break
            elif(i == lengthLines and args.get("name") != fullName): #if its the last entry the name is not on record
                print("Have a new target that needs to be added to the target file")
            i += 1

def getSchoolRecruitInfo(phoneCarrier,phoneNumber,team):
    teamname = str(team[0:len(team)-1]) # removes white space at the end
    teamName = teamname.replace(' ','-').lower() # replaces spaces with dashes and makes it lower case
    url = "https://247sports.com/college/{0}/Season/2021-Football/Targets/".format(teamName)
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"}

    req = Request(url,headers=header)
    page = urlopen(req).read()
    page_soup = soup(page,"html.parser")

    details = page_soup.findAll('li','ri-page__list-item')

    for i in  range (len(details)-1):
        name = details[i].find('div','recruit')

        if name != None:     
            athName = name.getText().strip()
            firstSpace = athName.find(' ')
            firstName = athName[0:firstSpace]
            athName = athName[firstSpace+1:]
            secondSpace = athName.find(' ')
            lastName = athName[0:secondSpace]
            athName = firstName + ' ' + lastName

            print('{:<75}'.format(name.getText()), end = " ")
        position = details[i].find('div','position')
        if position != None:
            print('{:<3}'.format(position.getText()), end = " ")
        interest = details[i].find('span', 'cool temp-status')
        if interest != None:
            print('{:<25}'.format(interest.getText()), end = " ")
        else:
            interest = details[i].find('span', 'warm temp-status')
            if interest != None:
                print('{:<25}'.format(interest.getText()), end = " ")
            else:
                interest = details[i].find('a', 'img-link')
                if interest != None:
                    print('{:<25}'.format(getSchoolCommitedTo(str(interest)) + " commit"), end = " ")
                    interest = getSchoolCommitedTo(str(interest))
                else:
                    interest = details[i].find('span','warmer temp-status')
                    if interest != None:
                        print('{:<25}'.format(interest.getText()), end = " ")
                    else:
                        interest = details[i].find('span', 'favorite temp-status')
                        if interest != None:
                            print('{:<25}'.format(interest.getText()), end = " ")
                        else:
                            interest = details[i].find('span', 'none temp-status')
                            if interest != None:
                                print('{:<25}'.format(interest.getText()), end = " ")

        starRating = details[i].find('span','score')
        if starRating != None:
            print('{:<10}'.format(starRating.getText()), end = " ")
            if type(interest) == str: # Means they are commited to a school and interest variable doesnt have a getText() function
                checkRankings(teamName,athName,position.getText(),interest, starRating.getText(), phoneCarrier, phoneNumber)
                #makeRecordsFile(teamName, name.getText(), position.getText(), interest, starRating.getText()) # NEED TO FIX TO WORK FOR MIAMI OH, TEXAS A&M and other weird ones.
            else:
                checkRankings(teamName,athName,position.getText(),interest.getText(),starRating.getText(),phoneCarrier,phoneNumber)
                #makeRecordsFile(teamName, name.getText(), position.getText(), interest.getText(), starRating.getText()) # NEED TO FIX TO WORK FOR MIAMI OH, TEXAS A&M and other weird ones.
        print(" ")

grabD1Teams()
createWindow()
