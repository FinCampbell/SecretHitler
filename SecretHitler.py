import random

"""
The GameBoard Object controls the overall playspace of the game. It sets up the game initially
and hosts the state object which is very frequently used for most elements of the game to
understand what is currently going on in the game.
"""


class GameBoard(object):

    def __init__(self, pl, isRandom, isRole,
                 isIntelligent):  # This defines the types of players which is included in the game
        self.state = GameState(len(pl), 6, 11)
        self.players = self.state.players
        self.playerList = pl
        self.roles = {}
        self.deck = []

        self.createRoles()
        self.assignRoles(isRandom, isRole, isIntelligent)

        self.updateState()

        self.deck = self.createDeck()

        self.updateState()

    # The Game supports a maximum of 10 players with differing numbers of both factions
    def createRoles(self):
        if self.players == 5:
            self.roles = {"Liberal": 3, "Fascist": 1, "Hitler": 1}
        elif self.players == 6:
            self.roles = {"Liberal": 4, "Fascist": 1, "Hitler": 1}
        elif self.players == 7:
            self.roles = {"Liberal": 4, "Fascist": 2, "Hitler": 1}
        elif self.players == 8:
            self.roles = {"Liberal": 5, "Fascist": 2, "Hitler": 1}
        elif self.players == 9:
            self.roles = {"Liberal": 5, "Fascist": 3, "Hitler": 1}
        elif self.players == 10:
            self.roles = {"Liberal": 6, "Fascist": 3, "Hitler": 1}

    # On initial creation of the Game Board object all players are assigned with their roles
    def assignRoles(self, isRandom, isRole, isIntelligent):
        c = 0
        for player in self.playerList:
            if any(x == 0 for x in self.roles.values()):
                for key in self.roles:
                    if self.roles[key] == 0:
                        del self.roles[key]
                        break
            role = random.choice(list(self.roles.keys()))
            if isRandom:
                self.playerList[c] = RandomPlayer(player, role, self)  # Different versions of the game use players
                # with different heuristics
            elif isRole:
                self.playerList[c] = RolePlayer(player, role, self)
            elif isIntelligent:
                self.playerList[c] = IntelligentRolePlayer(player, role, self)
            else:
                self.playerList[c] = Player(player, role)
            self.roles[role] -= 1
            c += 1

    # Since the Game Board Controls the rest of the game the option to update the state to a new one must be present
    def updateState(self):
        if not self.state.rolesApplied:  # This is where previously assigned roles are actually applied, once at the
            # start of the game

            playerId = 0

            for player in self.playerList:
                if player.role == "Liberal":
                    self.state.lib[player] = playerId
                    player.updateId(playerId)
                else:
                    self.state.fas[player] = playerId
                    player.updateId(playerId)
                playerId += 1
                self.state.rolesApplied = True

            self.state.playerDict = dict(list(self.state.lib.items()) + list(self.state.fas.items()))  # Both
            # dictionaries hold the Player object with and Id key
            self.state.IdDict = dict((y, x) for x, y in
                                     self.state.playerDict.items())  # And a Id int by player key, as both id's and
            # names are used interchangeably for different functions

        self.state.deck = self.deck
        self.state.setStateCode()

    # A Deck is created which will be utilised and shuffled in further methods
    def createDeck(self):

        deck = []

        # The deck is populated with policy objects
        for policy in range(0, self.state.libPol):
            deck.append(Policy("Liberal"))
        for policy in range(0, self.state.fasPol):
            deck.append(Policy("Fascist"))

        random.shuffle(deck)

        return deck


"""
Policy Objects are used to store the data for each card which is a name and an Id used similar to players, the id is
used as a numeric for creating state codes but the card name is used for readability
"""


class Policy(object):

    def __init__(self, name):
        self.name = name
        if name == "Liberal":
            self.id = 1
        else:
            self.id = 2

    def __str__(self):
        return self.name

    def getId(self):
        return self.id


"""
Player objects are inherited by objects which use apply certain heuristics to the actions taken in the object here

For example while the Player object contains the method to draw cards, which every subclass uses, they may then take
the result and use the differently. Such as selecting a random card, or an informed choice.

"""


class Player(object):

    def __init__(self, name, role, GB):
        self.name = name
        self.role = role
        self.GB = GB
        self.id = 0
        self.isPresident = False
        self.isChancellor = False
        self.isTermLimited = False

    def drawCards(self):

        hand = []

        if len(self.GB.state.deck) < 3:  # Reshuffle the deck if there is less than 3 cards.
            print("Shuffling in Progress")
            tmp = self.GB.state.deck + self.GB.state.discardDeck
            random.shuffle(tmp)
            self.GB.state.deck = tmp
            self.GB.state.discardDeck = []

        for x in range(0, 3):  # The game rules dictate the drawing of three cards
            try:
                hand.append(self.GB.state.deck.pop(x))
            except IndexError:
                hand.append(self.GB.state.deck.pop(0))

        return hand

    # In order to present options to the player we need to know all possible moves that player has from any given
    # position. In this case, everything that might happen should you choose to play a card that you have drawn.
    # The implications range from the played card and discard deck make up.
    def generatePSCHand(self, hand):

        currentState = self.GB.state.createString()

        PSC = []
        discard = []

        for x in hand:
            random.shuffle(hand)
            chosenCard = hand[0]
            discard.append(hand[1])
            discard.append(hand[2])
            self.discard(discard)
            discard = []
            self.play(chosenCard)
            chosenCard = None
            PSC.append(self.GB.state.createString())
            # self.flushHand()
            self.rollback(currentState)  # In order to generate we actually DO each of the options and then take the
            # current state of that possible future. In that case we then need to rollback any actions we took.

        return PSC

    # The other possible action is to elect a candidate. Candidates cannot be themselves, so this should limit who is
    # a possible candidate.
    def generatePSCElection(self, candidateList):

        currentState = self.GB.state.createString()

        PSC = []

        for x in candidateList:
            self.GB.state.chancellor = candidateList[x]
            PSC.append(self.GB.state.createString())
            # self.flushElection()
            self.rollback(currentState)  # Rollback needed

        count = 0
        for x in PSC:
            splitcode = x.split("/")
            if int(splitcode[8]) == int(splitcode[9]):  # Find any State Codes which have the chancellor elected the
                # same as the sitting president and delete it.
                del PSC[count]
            count += 1

        return PSC

    # Unused Functions
    def flushHand(self):
        self.GB.state.flushHand()

    def flushElection(self):
        self.GB.state.flushElection()

    # Utility Functions
    def rollback(self, stateCode):
        self.GB.state.rollback(stateCode)

    def discard(self, deck):
        self.GB.state.updateDiscardDeck(deck)

    def play(self, card):
        self.GB.state.updatePlayedCards(card)

    # Getters and Setters
    def updateId(self, id):
        self.id = id

    def getId(self):
        return self.id

    def __str__(self):
        return self.name


"""The GameState object is the most important and central to the games function. It concerns the current board state 
of the game. Each part of the game is tracked and, while it is much simplified from the real Secret Hitler game all 
the correct information exists here to adapt into a more complex program. 
"""


class GameState(object):

    def __init__(self, p, lp, fp):
        # I won't explain all of the different variables into detail but they will translate into a state code.
        self.players = p
        self.libPol = lp
        self.fasPol = fp
        self.lib = {}
        self.fas = {}
        self.playerDict = {}
        self.IdDict = {}
        self.deck = []
        self.discardDeck = []
        self.playedLib = 0
        self.playedFas = 0
        self.president = None
        self.chancellor = None
        self.termLimited = None
        self.votesFailed = 0
        self.veto = False
        self.statecode = None

        self.rolesApplied = False

    # State Code Creator. The State Code is central information in the game. We can jump around states provided that
    # a code if given for where you want to go. A full explanation of the state code will be given in the report.
    def createString(self):
        code = str(self.players) + "/" + str(self.libPol) + "." + str(self.fasPol) + "/"
        for lib in self.lib:
            code = code + str(lib.getId()) + "-"
        code += "/" # State Code separator
        for fas in self.fas:
            code = code + str(fas.getId()) + "-"
        code += "/"
        for policy in self.deck:
            code = code + str(policy.getId())
        code += "/"
        for policy in self.discardDeck:
            code = code + str(policy.getId())
        code += "/"
        code += str(self.playedLib)
        code += "/"
        code += str(self.playedFas)
        code += "/"
        if self.president is None:
            code += "X"
        else:
            code = code + str(self.president)
        code += "/"
        if self.chancellor is None:
            code += "X"
        else:
            code = code + str(self.chancellor)
        code += "/"
        if self.termLimited is None:
            code += "X"
        else:
            code = code + str(self.termLimited)

        # Essentially we have converted each variable into a number than we can output and use.

        return code

    # Read String is the converse to Creation. This takes an output of the previous string and then sets all the
    # variables as per they have been encoded.
    #
    # Using the split character we can deal with each part of the state code individually.
    def readString(self, string):
        splitstring = string.split("/")

        self.players = splitstring[0]

        polNum = splitstring[1].split(".")
        self.libPol = polNum[0]
        self.fasPol = polNum[1]

        deck = []
        for x in splitstring[4]:
            if x == str(1):
                deck.append(Policy("Liberal"))
            else:
                deck.append(Policy("Fascist"))

        self.deck = deck

        deck = []
        for x in splitstring[5]:
            if x == str(1):
                deck.append(Policy("Liberal"))
            else:
                deck.append(Policy("Fascist"))

        self.discardDeck = deck

        self.playedLib = int(splitstring[6])
        self.playedFas = int(splitstring[7])

        self.president = int(splitstring[8])
        try:
            self.chancellor = int(splitstring[9])
        except ValueError:  # We must handle errors here since there are times where we cannot convert splitstring[9]
            # to int as it is a string "X". In these scenarios we have to set it manually.
            self.chancellor = "X"
        try:
            self.termLimited = int(splitstring[10])
        except ValueError:
            self.termLimited = "X"

        self.setStateCode()

    # Update Functions
    def updateDiscardDeck(self, deck):
        for x in deck:
            self.discardDeck.append(x)

    def updatePlayedCards(self, card):
        if card.getId() == 1:
            self.playedLib += 1
        else:
            self.playedFas += 1

    # Unused Functions
    def flushHand(self):
        self.discardDeck = []
        self.playedLib = 0
        self.playedFas = 0

    def flushElection(self):
        self.chancellor = "X"

    # Utility Functions
    def rollback(self, stateCode):
        self.readString(stateCode)

    # Getters and Setters
    def setStateCode(self):

        self.statecode = self.createString()

    def getStateCode(self):

        return self.statecode


"""
Random Players are the first class of Heuristic-Utilising Players. They choose every action they take as random.
These are not efficient as Liberals might choose a Fascist Policy and vice versa.

This is achieved by randomly shuffling every possible code and then taking the first one in the list.
"""


class RandomPlayer(Player):

    def __init__(self, name, role, GB):
        super().__init__(name, role, GB) # Inherits the Player object as we still need their functions

    # Used to check in console the type of player.
    def areRandom(self):
        return self.name + " is a Random Actor"

    # Takes a list of candidates for election (Other Players in the Game) and creates all state codes for them.
    # President Function
    def elect(self, candidateList):
        # del candidateList[self]
        PSC = self.generatePSCElection(candidateList)
        outcome = self.selectOutcome(PSC)  # Select Outcome is the Random Selection Function
        self.GB.state.readString(outcome)

    # Draws Cards and Chooses one. Chancellor Function
    def drawAndChoose(self):
        hand = self.drawCards()
        PSC = self.generatePSCHand(hand)
        outcome = self.selectOutcome(PSC)  # Random Selector Function
        self.GB.state.readString(outcome)

    # Select a Random State Code from list of possible.
    def selectOutcome(self, PSC):
        random.shuffle(PSC)
        chosenGameState = PSC[0]
        return chosenGameState

    def __str__(self):
        return str(self.name)


"""
Role Players are the second Heuristic Used in the game. These always play to the role that they have been given. 
Fascists will always play Fascist Cards when possible and Vice-Versa.  The Chance that either team wins is much more 
balanced.

This is achieved by defining a "Goal". Working out if the next code will reach that goal and then choosing any State
Code which does.
"""


class RolePlayer(Player):

    def __init__(self, name, role, GB):
        super().__init__(name, role, GB)

    # Used to check in console the type of player.
    def areRole(self):
        return self.name + " is a Role Actor"

    # Elections are still Random. You don't know roles so you can't "Always elect someone on your team"
    # President Function
    def elect(self, candidateList):
        # del candidateList[self]
        PSC = self.generatePSCElection(candidateList)
        outcome = self.selectOutcome(PSC)
        self.GB.state.readString(outcome)

    # Drawing and making a choice based off the role you've been given.
    def drawAndChoose(self):
        hand = self.drawCards()
        PSC = self.generatePSCHand(hand)

        actions = []

        # Define the Goal
        if self.role == "Liberal":
            goal = "l+1"
        else:
            goal = "f+1"

        # Define the Current Played Cards to compare possible futures to
        currentlib = self.GB.state.playedLib
        currentfas = self.GB.state.playedFas

        for x in PSC:
            splitstring = x.split("/")
            lib = splitstring[6]
            fas = splitstring[7]
            if int(lib) - currentlib == 1:
                actions.append("l+1")  # Create a list of actions and which goal each one fulfils.
            elif int(fas) - currentfas == 1:
                actions.append("f+1")

        count = 0
        outcome = None
        for x in actions:
            if x == goal:
                outcome = PSC[count]  # Selects as outcome the Action which Meets the goal
            count += 1

        if outcome is None:
            outcome = self.selectOutcome(PSC)  # Can't find one? Random Select..

        self.GB.state.readString(outcome)

    # Still need a random selector in cases where it is not possible to fulfil the role.
    def selectOutcome(self, PSC):
        random.shuffle(PSC)
        chosenGameState = PSC[0]
        return chosenGameState

    def __str__(self):
        return str(self.name)


"""
Intelligent Players are the closest to a system that then might be used to apply some kind of Reinforced Learning 
Algorithm on in order to increase game performance even further. They keep a suspect value for each other player in the 
game and make their decision on who to elect based off their knowledge of each other player in the game.

To achieve this we adapt the last player but every time an action is take by ANOTHER player it is broadcasted. If it is
a "Bad" Action. Sus is increased on that player. If it is a good action the it is reduced, but by a smaller amount as
bad actions are much worse than good actions. This would be an interesting parameter to change however. 

"""


class IntelligentRolePlayer(Player):

    def __init__(self, name, role, GB):
        super().__init__(name, role, GB)
        self.susDict = {}  # This requires a dictionary of players and the value of sus that we have on all of them
        self.otherPlayers = None

    # Used to check in console the type of player.
    def areRole(self):
        return self.name + " is a Intelligent Role Actor"

    # Populate the initial values of sus
    def populate(self):
        self.otherPlayers = dict(self.GB.state.playerDict)  # Fill other players with all players
        for x in self.otherPlayers:
            if str(x) == str(self.name):
                del self.otherPlayers[x]  # Remove self. Can't have sus on self as you know your own role.
                break

        for x in self.otherPlayers:
            self.susDict[x] = 0

    # Elect with regards to sus values
    def elect(self, candidateList):
        # del candidateList[self]

        PSC = self.generatePSCElection(candidateList)

        outcome = None

        print(self.role)
        if self.role == "Liberal":  # Different depending on the role you are. Liberals always elect LEAST sus
            key = min(self.susDict, key=self.susDict.get)
            id = self.GB.state.playerDict.get(key)
            for x in PSC:
                splitcode = x.split("/")
                if int(id) == int(splitcode[9]):
                    outcome = x
        else:
            key = max(self.susDict, key=self.susDict.get)  # Fascists always elect the MOST sus
            id = self.GB.state.playerDict.get(key)
            for x in PSC:
                splitcode = x.split("/")
                if int(id) == int(splitcode[9]):
                    outcome = x

        # outcome = self.selectOutcome(PSC)
        self.GB.state.readString(outcome)

    # Leftover function. Don't think I need. Scared to delete.
    def selectOutcome(self, PSC):
        random.shuffle(PSC)
        chosenGameState = PSC[0]
        return chosenGameState

    # Same implementation of role based card choice from above.
    def drawAndChoose(self):
        hand = self.drawCards()
        PSC = self.generatePSCHand(hand)

        actions = []

        if self.role == "Liberal":
            goal = "l+1"
        else:
            goal = "f+1"

        currentlib = self.GB.state.playedLib
        currentfas = self.GB.state.playedFas

        for x in PSC:
            splitstring = x.split("/")
            lib = splitstring[6]
            fas = splitstring[7]
            if int(lib) - currentlib == 1:
                actions.append("l+1")
            elif int(fas) - currentfas == 1:
                actions.append("f+1")

        count = 0
        outcome = None
        for x in actions:
            if x == goal:
                outcome = PSC[count]
            count += 1

        if outcome is None:
            outcome = self.selectOutcome(PSC)

        self.GB.state.readString(outcome)

    # When an action is broadcasted every player will use this function to adjust their sus values.
    def updateSus(self, chancellor, played):

        if played == 1:
            self.susDict[chancellor] -= 2
            if self.susDict[chancellor] < 0:
                self.susDict[chancellor] = 0
        elif played == 2:
            self.susDict[chancellor] += 5  # These could be interesting to change?

    def __str__(self):
        return str(self.name)


"""
Game Player is a class which takes all of the above and runs games based on them. Like an organiser. This is where all 
of my parameters will feed into and all of the programs outputs come out to.
"""


class GamePlayer(object):

    def __init__(self, players, isRandom, isRole, isIntelligent):
        self.players = players
        self.isRandom = isRandom
        self.isRole = isRole
        self.isIntelligent = isIntelligent
        self.GB = None
        self.round = 0
        self.subround = 0
        self.seats = []
        self.seatPointer = 0
        self.president = None
        self.chancellor = None
        self.wincon = 5
        self.libWinCount = 0
        self.fasWinCount = 0

        for x in range(0, 100):
            self.game()
            self.reset()

    # Since we are running multiple games then we will need to totally reset everything when playing a new game
    def reset(self):
        self.GB = None
        self.round = 0
        self.subround = 0
        self.seats = []
        self.seatPointer = 0
        self.president = None
        self.chancellor = None

    # Runs a copy of the game. Round one if slightly different and should ALWAYS happen.
    # Future rounds happen if win condition not met.
    def game(self):
        # Round One
        self.GB = GameBoard(self.players, self.isRandom, self.isRole, self.isIntelligent)
        if self.isIntelligent:
            for x in self.GB.state.playerDict:
                x.populate()
        self.defineOrderInit()
        self.president = self.callIdDict(self.GB.state.president)
        self.statusUpdate()

        self.elect()

        self.statusUpdate()

        self.lastStateCode = self.GB.state.createString()
        self.chancellor.drawAndChoose()
        if self.isIntelligent:
            self.broadcast() # Broadcasting for Intelligent Player Games

        self.statusUpdate()

        self.newPres()
        # End of round One

        while self.GB.state.playedLib < self.wincon and self.GB.state.playedFas < self.wincon: # Keep playing until Win
            # Condition is met.
            self.statusUpdate()
            self.elect()
            self.statusUpdate()
            self.lastStateCode = self.GB.state.createString()
            self.chancellor.drawAndChoose()   # Chancellor Chooses Cards.
            if self.isIntelligent:
                self.broadcast()
            self.statusUpdate()
            self.newPres()

        # End of Game output.
        print("Liberal Policy Played = " + str(self.GB.state.playedLib))
        print("Fascist Policy Played = " + str(self.GB.state.playedFas))
        if self.GB.state.playedLib > self.GB.state.playedFas:
            print("Lib Win")
            self.libWinCount += 1
        else:
            print("Fas Win")
            self.fasWinCount += 1

        if self.isIntelligent:
            for x in self.GB.state.playerDict:
                print(x.susDict)

    # Initial function for defining a seating arrangement of players. President rotates.
    def defineOrderInit(self):
        self.seats = list(self.GB.state.playerDict)
        random.shuffle(self.seats)
        self.GB.state.president = self.callPlayerDict(self.seats[self.seatPointer])

    # Shift over the president to next Player.
    def newPres(self):
        self.seatPointer += 1
        if self.seatPointer >= len(self.seats):
            self.seatPointer = 0
        self.GB.state.termLimited = self.GB.state.president
        self.GB.state.president = self.callPlayerDict(self.seats[self.seatPointer])
        self.GB.state.chancellor = "X"
        self.subround = 0
        self.round += 1

    # President Chooses to Elect Player which activates player object functions
    def elect(self):
        self.president = self.callIdDict(self.GB.state.president)
        candidateList = self.GB.state.playerDict
        self.president.elect(candidateList)
        self.chancellor = self.callIdDict(self.GB.state.chancellor)

    # Broadcasts actions to appropriate players so they can update their internal sus values.
    def broadcast(self):
        last = self.lastStateCode.split("/")
        lastLib = last[6]
        lastFas = last[7]

        currentStateCode = self.GB.state.createString
        current = currentStateCode().split("/")
        currentLib = current[6]
        currentFas = current[7]

        if int(currentLib) - int(lastLib) == 1:
            played = 1
        elif int(currentFas) - int(lastFas) == 1:
            played = 2

        broadCastDict = dict(self.GB.state.playerDict)
        broadCastDict.pop(self.chancellor)
        for x in broadCastDict:
            x.updateSus(self.chancellor, played)

    # Frequent Call Functions
    def callPlayerDict(self, p):
        return self.GB.state.playerDict.get(p)

    def callIdDict(self, id):
        return self.GB.state.IdDict.get(id)

    # Frequent Print Statements. Output to Console
    def currentStateCode(self):
        return "Current State: " + self.GB.state.createString()

    def currentLeadership(self):
        return "President: " + str(self.callIdDict(self.GB.state.president)) + "\nChancellor: " + str(
            self.callIdDict(self.GB.state.chancellor))

    def statusUpdate(self):

        print("Round: " + str(self.round) + " | SubRound: " + str(self.subround))
        self.subround += 1

        print(self.currentStateCode())
        print(self.currentLeadership())

        print("---------------------------")

    def getWinStats(self):

        print("Liberal Win Count " + str(self.libWinCount))
        print("Fascist Win Count " + str(self.fasWinCount))
