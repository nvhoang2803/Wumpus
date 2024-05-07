import numpy as np
from pygame_functions import *
from PIL import Image
import itertools
from datetime import datetime


def createLabel(flags):
    label = np.array([[[None, None, None, None, None] for j in range(len(flags))] for i in range(len(flags))])
    # (stench, breeze, wumpus, pit, gold)
    for i in range(len(flags)):
        for j in range(len(flags)):
            if flags[i, j, 0]:
                label[i, j, 0] = makeSprite("img/stench.png")

            if flags[i, j, 1]:
                label[i, j, 1] = makeSprite("img/breeze.png")

            if flags[i, j, 2]:
                label[i, j, 2] = makeSprite("img/wumpus.png")
                continue

            if flags[i, j, 3]:
                label[i, j, 3] = makeSprite("img/pit.png")
                continue

            if flags[i, j, 4]:
                label[i, j, 4] = makeSprite("img/gold.png")

    return label


def outputMap(flags, name, agent):
    size = len(flags)
    with open(name, 'w') as f:
        f.write(str(size)+'\n')
        # (stench, breeze, wumpus, pit, gold)
        for j in range(size-1, -1, -1):
            for i in range(size):
                stt = ''
                if flags[i, j, 0]:
                    stt += 'S'
                if flags[i, j, 1]:
                    stt += 'B'
                if flags[i, j, 2]:
                    stt += 'W'
                elif flags[i, j, 3]:
                    stt += 'P'
                elif flags[i, j, 4]:
                    stt += 'G'
                if i == agent[0] & j == agent[1]:
                    stt += 'A'
                sort_stt = sorted(stt)
                stt = "".join(sort_stt)
                if stt == '':
                    stt = '-'
                f.write(stt)
                if i == size - 1:
                    continue
                f.write('.')
            f.write('\n')


def inputMap(name):
    with open(name, 'r') as f:
        size = f.readline()
        size = int(size)
        flags = np.array([[[False, False, False, False, False] for j in range(size)] for i in range(size)])
        labels = np.array([[None for j in range(size)] for i in range(size)])

        pits = 0
        wumpus = 0
        gold = 0
        agent = None
        # (stench, breeze, wumpus, pit, gold)
        for j in range(size - 1, -1, -1):

            labels[:, j] = f.readline().split('.')
            for i in range(size):
                if labels[i, j] == '-':
                    continue

                if 'S' in labels[i, j]:
                    flags[i, j, 0] = True

                if 'B' in labels[i, j]:
                    flags[i, j, 1] = True

                if 'W' in labels[i, j]:
                    flags[i, j, 2] = True
                    wumpus += 1
                    continue

                if 'P' in labels[i, j]:
                    flags[i, j, 3] = True
                    pits += 1
                    continue

                if 'G' in labels[i, j]:
                    flags[i, j, 4] = True
                    gold += 1
                    continue

                if 'A' in labels[i, j]:
                    agent = np.array([i, j])
    if agent is None:
        agent = np.array([0, 0])
    return flags, wumpus, pits, gold, agent


def moveForward(x, y, KB, game):
    flag = game.flags[x, y]
    if not flag[1] and not flag[0]:
        if game.character.goAhead(game.size, game.explored):
            x, y = game.character.getIter()
            game.score.move()
            return True, x, y
        adj = getAdj(x, y, game.size)
        for a in adj:
            i, j = a[:2]
            if game.explored[i, j]:
                continue
            game.character.goto(i, j)
            game.score.move()
            return True, i, j
        return False, x, y
    if flag[1]:
        adj = getAdj(x, y, game.size)
        for a in adj:
            i, j = a[:2]
            if game.explored[i, j]:
                continue
            if PL_Resolution(KB, '-P'+str(i)+','+str(j)):
                if flag[0]:
                    return False, x, y
                game.character.goto(i, j)
                game.score.move()
                return True, i, j

    if flag[0]:
        adj = getAdj(x, y, game.size)
        for a in adj:
            i, j = a[:2]
            if game.explored[i, j]:
                continue
            if PL_Resolution(KB, '-W' + str(i) + ',' + str(j)):
                if flag[1]:
                    return False, x, y
                game.character.goto(i, j)
                game.score.move()
                return True, i, j

    return False, x, y


def setSymbol(isNot, symbol, i, j):
    s = ''
    if isNot:
        s = s + '-'
    if symbol == 2:
        tag = 'W'
    if symbol == 3:
        tag = 'P'
    return s + tag + str(i) + ',' + str(j)


def getX(s):
    if s[0] == '-':
        s = s.split(s[0], 1)[1]
        return False, s
    return True, s


def contradiction(s1, s2):
    isNot1, x1 = getX(s1)
    isNot2, x2 = getX(s2)
    if isNot1 == (not isNot2):
        if x1 == x2:
            return True
    return False


def PL_Resolve(C1, C2):
    clauses = []
    ls = []
    for c1 in C1:
        for c2 in C2:
            if contradiction(c1, c2):
                ls.append([c1, c2])
    for l in ls:
        cl = []
        for a in C1:
            if a != l[0]:
                cl.append(a)
        for b in C2:
            if b != l[1]:
                cl.append(b)
        clauses.append(cl)
    return clauses


def PL_Resolution(KB, a):
    isNot, tag, i, j = getSymbol(a)
    _, x = getX(a)
    clauses = KB.copy()
    clauses.append([setSymbol(not isNot, tag, i, j)])
    while True:
        new = []
        for cl in itertools.combinations(clauses, 2):
            a = cl[0]
            b = cl[1]
            can = False
            for _a in a:
                _, x2 = getX(_a)
                if x2 == x:
                    can = True
            for _b in b:
                _, x2 = getX(_b)
                if x2 == x:
                    can = True
            if not can:
                continue

            resolvents = PL_Resolve(a, b)
            for r in resolvents:
                if len(r) == 0:
                    return True
                else:
                    new.append(r)
        clauses_old = len(clauses)
        for n in new:
            diff = True
            for k in clauses:
                if n == k:
                    diff = False
            if diff:
                clauses.append(n)
        if len(clauses) == clauses_old:
            return False


def PL(x, y, game):
    # Set up
    KB = []
    # stench, breeze, wumpus, pit
    symbols = np.array([[[None, None, None, None] for j in range(game.size)] for i in range(game.size)])
    exploredRoom = np.array([[False for j in range(game.size)] for i in range(game.size)])
    exploredRoom[x, y] = True
    symbols[x, y, :] = False
    flag = game.flags[x, y]
    if isBreeze(flag) or isStench(flag) or isWumpus(flag) or isPit(flag):
        print("Climbing out the cave !!!")
        game.climbing_out()
        game.score.climb_out()
        return

    while True:
        flag = game.flags[x, y]
        if isWumpus(flag) or isPit(flag):
            print("GAME OVER!")
            print("YOU LOSE !!!")
            game.score.die()
            return
        if isGold(flag):
            pause(500)
            game.grabGold()
        if isStench(flag):
            symbols[x, y, 0] = True
        if isBreeze(flag):
            symbols[x, y, 1] = True

        clauses = getClauses(x, y, game, exploredRoom)
        for cl in clauses:
            KB.append(cl)

        if isStench(flag):
            nearWumpus(x, y, KB, game, exploredRoom)

        if game.gold == 0 and game.wumpus == 0:
            print("GAME OVER!")
            print("YOU WON !!!")
            return
        old_x = x
        old_y = y

        moved, x, y = moveForward(x, y, KB, game)
        if not moved:
            x, y = findPath(x, y, KB, symbols, exploredRoom, game)

        if old_x == x and old_y == y:
            print("Climbing out the cave !!!")
            game.climbing_out()
            game.score.climb_out()
            return
        exploredRoom[x, y] = True
        game.exploredRoom(x, y)
        tick(5)


def findPath(x, y, KB, symbols, explored, game):
    queue = []
    adj = getAdj(x, y, game.size)
    for ad in adj:
        i, j = ad[:2]
        if explored[i, j]:
            queue.append([[i, j]])
    notMove = []
    t = datetime.now().second
    while True:
        if len(queue) == 0:
            return x, y
        current_path = queue.pop(0)
        cur_x, cur_y = current_path[-1][:2]
        adj = getAdj(cur_x, cur_y, game.size)
        for ad in adj:
            i, j = ad[:2]
            r = [i, j]
            had = False
            for c in current_path:
                if c == r:
                    had = True
                    break
            for n in notMove:
                if n == r:
                    had = True
                    break
            for q in queue:
                if r == q[-1]:
                    had = True
                    break
            if not had:
                new_path = current_path.copy()
                new_path.append([i, j])
                if not explored[i, j]:
                    a, b = new_path[-2][:2]
                    if not isStench(game.flags[a, b]) and not isBreeze(game.flags[a, b]):
                        path = new_path
                        for p in path:
                            i, j = p[:2]
                            game.character.goto(i, j)
                            game.score.move()
                            tick(10)
                        x, y = game.character.getIter()
                        return x, y
                    if PL_Resolution(KB, 'P' + str(i) + ',' + str(j)):
                        notMove.append([i, j])
                        continue
                    elif PL_Resolution(KB, '-P'+str(i)+','+str(j)):
                        if PL_Resolution(KB, '-W'+str(i)+','+str(j)):
                            path = new_path
                            for p in path:
                                i, j = p[:2]
                                game.character.goto(i, j)
                                game.score.move()
                                tick(10)
                            x, y = game.character.getIter()
                            return x, y
                        elif PL_Resolution(KB, 'W'+str(i)+','+str(j)):
                            path = new_path
                            path.pop(-1)
                            for p in path:
                                i, j = p[:2]
                                game.character.goto(i, j)
                                game.score.move()
                                tick(10)
                            x, y = game.character.getIter()
                            return x, y
                    notMove.append([i, j])
                else:
                    queue.append(new_path)
    return x, y


def nearWumpus(x, y, KB, game, exploredRoom):
    adj = getAdj(x, y, game.size)
    for a in adj:
        i, j = a[:2]
        if PL_Resolution(KB, 'W'+str(i)+','+str(j)):
            if not game.explored[i, j]:
                game.shoot(i, j)
                exploredRoom[i, j] = True


def getSymbol(s):
    isNot = False
    symbol = None  # stench = 0 , breeze = 1, wumpus = 2, pit = 3
    i = 0
    if s[i] == '-':
        isNot = True
        s = s.split(s[0], 1)[1]

    if s[i] == 'P':
        symbol = 3
    elif s[i] == 'W':
        symbol = 2
    elif s[i] == 'B':
        symbol = 1
    elif s[i] == 'S':
        symbol = 0
    else:
        return None, None, None, None
    s = s.split(s[0], 1)[1]

    ls = s.split(',', 1)
    x = int(ls[0])
    y = int(ls[1])
    return isNot, symbol, x, y


def getClauses(x, y, game, exploredRoom):
    size = game.size
    flag = game.flags[x, y]
    clauses = []
    if isStench(flag):
        adj = getAdj(x, y, size)
        cl = []
        for a in adj:
            i, j = a[:2]
            if exploredRoom[i, j]:
                continue
            cl.append('W'+str(i)+','+str(j))
        clauses.append(cl)
    else:
        adj = getAdj(x, y, size)
        for a in adj:
            i, j = a[:2]
            if exploredRoom[i, j]:
                continue
            cl = ['-W' + str(i) + ',' + str(j)]
            clauses.append(cl)
    if isBreeze(flag):
        adj = getAdj(x, y, size)
        cl = []
        for a in adj:
            i, j = a[:2]
            if exploredRoom[i, j]:
                continue
            cl.append('P' + str(i) + ',' + str(j))
        clauses.append(cl)
    else:
        adj = getAdj(x, y, size)
        for a in adj:
            i, j = a[:2]
            if exploredRoom[i, j]:
                continue
            cl = ['-P' + str(i) + ',' + str(j)]
            clauses.append(cl)
    return clauses


def isBreeze(flag):
    return flag[1]


def isStench(flag):
    return flag[0]


def isWumpus(flag):
    return flag[2]


def isPit(flag):
    return flag[3]


def isGold(flag):
    return flag[4]


def create_random_map(size=10, pits=0, wumpus=0, gold=0):
    """
    :param gold: amount of gold
    :param wumpus: amount of wumpus
    :param pits: amount of wumpus
    :param size of wumpus map (Default size = 10)
    :return: array[size][size] which contains (stench, breeze, wumpus, pit, gold)
    """
    label = np.array([[[None, None, None, None, None] for j in range(size)] for i in range(size)])
    flags = np.array([[[False, False, False, False, False] for j in range(size)] for i in range(size)])

    for _ in range(pits):
        x, y = np.random.choice(size, 2)
        while flags[x, y, 3]:
            x, y = np.random.choice(size, 2)
        label[x, y, 3] = makeSprite("img/pit.png")
        flags[x, y, 3] = True
        arr = getAdj(x, y, size)
        if len(arr) != 0:
            for a, b in arr:
                label[a, b, 1] = makeSprite("img/breeze.png")
                flags[a, b, 1] = True

    for _ in range(wumpus):
        x, y = np.random.choice(size, 2)
        while flags[x, y, 2] | flags[x, y, 3]:
            x, y = np.random.choice(size, 2)
        label[x, y, 2] = makeSprite("img/wumpus.png")
        flags[x, y, 2] = True
        arr = getAdj(x, y, size)
        if len(arr) != 0:
            for a, b in arr:
                label[a, b, 0] = makeSprite("img/stench.png")
                flags[a, b, 0] = True
    for _ in range(gold):
        x, y = np.random.choice(size, 2)
        while flags[x, y, 4] | flags[x, y, 2] | flags[x, y, 3]:
            x, y = np.random.choice(size, 2)
        label[x, y, 4] = makeSprite("img/gold.png")
        flags[x, y, 4] = True

    x, y = np.random.choice(size, 2)
    while flags[x, y, 4] | flags[x, y, 2] | flags[x, y, 3]:
        x, y = np.random.choice(size, 2)

    agent = [x, y]

    return label, flags, agent


def showlabel(label):
    for _ in label:
        if _ is not None:
            showSprite(_)


def getAdj(x, y, size):
    adj = []
    for i in [x - 1, x + 1]:
        if i < 0 or i > size - 1:
            continue
        adj.append([i, y])
    for j in [y - 1, y + 1]:
        if j < 0 or j > size - 1:
            continue
        adj.append([x, j])
    return adj


class Character:
    def __init__(self, length, room_length, size):
        self.x_pos = 0
        self.y_pos = 0

        self.size = size
        self.map_length = length

        self.rl = room_length

        self.sprite = makeSprite("img/ch1.png")
        addSpriteImage(self.sprite, "img/ch2.png")
        addSpriteImage(self.sprite, "img/ch3.png")
        addSpriteImage(self.sprite, "img/ch4.png")
        self.sprite.changeImage(1) # Facing right

    def move(self, x, y):
        self.x_pos = x
        self.y_pos = y
        moveSprite(self.sprite, self.x_pos, self.y_pos)

    def show(self):
        showSprite(self.sprite)

    def getPosition(self):
        return self.x_pos, self.y_pos

    def getIter(self):
        return self.x_pos // self.rl, self.size - self.y_pos // self.rl - 1

    def currentImage(self):
        return self.sprite.currentImage

    def changeImage(self, index):
        changeSpriteImage(self.sprite, index)

    def Up(self):
        if self.currentImage() == 3:
            if self.y_pos != 0:
                self.y_pos = self.y_pos - self.rl
                moveSprite(self.sprite, self.x_pos, self.y_pos)
                showSprite(self.sprite)
                return True
        else:
            self.changeImage(3)
        return False

    def Down(self):
        if self.currentImage() == 0:
            if self.y_pos != self.map_length - self.rl:
                self.y_pos = self.y_pos + self.rl
                moveSprite(self.sprite, self.x_pos, self.y_pos)
                showSprite(self.sprite)
                return True
        else:
            self.changeImage(0)
        return False

    def Left(self):
        if self.currentImage() == 2:
            if self.x_pos != 0:
                self.x_pos = self.x_pos - self.rl
                moveSprite(self.sprite, self.x_pos, self.y_pos)
                showSprite(self.sprite)
                return True
        else:
            self.changeImage(2)
        return False

    def Right(self):
        if self.currentImage() == 1:
            if self.x_pos != self.map_length - self.rl:
                self.x_pos = self.x_pos + self.rl
                moveSprite(self.sprite, self.x_pos, self.y_pos)
                showSprite(self.sprite)
                return True
        else:
            self.changeImage(1)
        return False

    def goAhead(self, size, exploredRoom):
        cur = self.currentImage()
        i, j = self.getIter()
        if cur == 0:
            if j - 1 < 0 or exploredRoom[i, j - 1]:
                return False
            return self.Down()
        elif cur == 1:
            if i + 1 == size or exploredRoom[i + 1, j]:
                return False
            return self.Right()
        elif cur == 2:
            if i - 1 < 0 or exploredRoom[i - 1, j]:
                return False
            return self.Left()
        else:
            if j + 1 == size or exploredRoom[i, j + 1]:
                return False
            return self.Up()

    def grabGold(self):
        pass

    def goto(self, i, j):
        x, y = self.getIter()
        a = i - x
        b = j - y
        if a == 0:
            if b == 1:
                if not self.Up():
                    #tick(2)
                    self.Up()
            else:
                if not self.Down():
                    #tick(2)
                    self.Down()
        else:
            if a == 1:
                if not self.Right():
                    #tick(2)
                    self.Right()
            else:
                if not self.Left():
                    #tick(2)
                    self.Left()

    def shoot(self):
        arrow = makeSprite("img/arrow.png")
        sound = makeSound("sound/shoot.ogg")
        x = self.x_pos
        y = self.y_pos
        moveSprite(arrow, x, y)
        if self.currentImage() == 0:
            transformSprite(arrow, 180, 1)
            showSprite(arrow)
            playSound(sound)
            for i in range(50):
                y = y + 3
                moveSprite(arrow, x, y)
            killSprite(arrow)

        elif self.currentImage() == 1:
            transformSprite(arrow, 270, 1)
            showSprite(arrow)
            playSound(sound)
            for i in range(50):
                x = x + 3
                moveSprite(arrow, x, y)
            killSprite(arrow)
        elif self.currentImage() == 2:
            transformSprite(arrow, 90, 1)
            showSprite(arrow)
            playSound(sound)
            for i in range(50):
                x = x - 3
                moveSprite(arrow, x, y)
            killSprite(arrow)
        elif self.currentImage() == 3:
            showSprite(arrow)
            playSound(sound)
            for i in range(50):
                y = y - 3
                moveSprite(arrow, x, y)
            killSprite(arrow)

    def turnthenshoot(self, i, j):
        x, y = self.getIter()
        a = i - x
        b = j - y
        currentStatus = self.currentImage()
        if a == 0:
            if b == 1:
                if currentStatus == 3:
                    self.shoot()
                else:
                    self.changeImage(3)
                    self.shoot()
            else:
                if currentStatus == 0:
                    self.shoot()
                else:
                    self.changeImage(0)
                    self.shoot()
        else:
            if a == 1:
                if currentStatus == 1:
                    self.shoot()
                else:
                    self.changeImage(1)
                    self.shoot()
            else:
                if currentStatus == 2:
                    self.shoot()
                else:
                    self.changeImage(2)
                    self.shoot()

    def update(self):
        hideSprite(self.sprite)
        showSprite(self.sprite)


class Score:
    def __init__(self):
        self.point = 0

    def move(self):
        self.point -= 10

    def pick_up_gold(self):
        self.point += 100

    def shoot_arrow(self):
        self.point -= 100

    def die(self):
        self.point -= 10000

    def climb_out(self):
        self.point += 10

    def total_score(self):
        return self.point

    def reset(self):
        self.point = 0


class TheWumpusWorld:
    def __init__(self, size):
        room = Image.open("./img/room.jpg")
        ar = np.asarray(room)

        self.rl = ar.shape[0]
        self.map_length = self.rl * size
        self.size = size
        self.label = []
        self.flags = []
        self.wumpus = 0
        self.gold = 0
        self.score = Score()
        self.start_x = 0
        self.start_y = 0

        screenSize(self.map_length, self.map_length, 0, 0)
        setWindowTitle("The Wumpus World")

        self.character = Character(self.map_length, self.rl, self.size)
        self.explored = np.array([[False for j in range(size)] for i in range(size)])
        self.rooms = [[makeSprite("./img/room.jpg") for j in range(size)] for i in range(size)]

    def addLabel(self, label, flags):
        self.flags = flags
        self.label = label
        for i in range(self.size):
            for j in range(self.size):
                if flags[i, j, 2]:
                    self.wumpus = self.wumpus + 1
                if flags[i, j, 4]:
                    self.gold = self.gold + 1
        self.customizeRoom(self.label)

    def setPositionAgent(self, agent_x, agent_y):
        self.start_x = agent_x
        self.start_y = agent_y
        x_pos = agent_x * self.rl
        y_pos = (self.size - agent_y - 1) * self.rl
        self.exploredRoom(agent_x, agent_y)
        self.character.move(x_pos, y_pos)
        self.character.show()

    def customizeRoom(self, label):
        for i in range(self.size):
            for j in range(self.size):
                x_pos = i * self.rl
                y_pos = (self.size - j - 1) * self.rl
                addSpriteImage(self.rooms[i][j], "img/explored_room.jpg")
                moveSprite(self.rooms[i][j], x_pos, y_pos)
                for _ in label[i, j]:
                    if _ is not None:
                        moveSprite(_, x_pos, y_pos)
        showSprite(self.rooms[:][:])

    def getMapSize(self):
        return self.map_length, self.map_length

    def exploredRoom(self, i, j):
        if not self.explored[i][j]:
            self.explored[i][j] = True
            self.updateRoom(i, j)
            showlabel(self.label[i, j])
            self.character.update()

    def updateRoom(self, i, j):
        changeSpriteImage(self.rooms[i][j], 1)

    def getIterator(self, x_pos, y_pos):
        return x_pos // self.rl, self.size - y_pos // self.rl - 1

    def grabGold(self):
        x_pos, y_pos = self.character.getPosition()
        i, j = self.getIterator(x_pos, y_pos)
        if self.label[i, j, 4] is not None:
            killSprite(self.label[i, j, 4])
            self.label[i, j, 4] = None
            self.gold -= 1
            self.character.grabGold()

            self.score.pick_up_gold()

    def shoot(self, i, j):
        self.character.turnthenshoot(i, j)
        self.score.shoot_arrow()
        if self.label[i, j, 2]:
            self.exploredRoom(i, j)
            killSprite(self.label[i, j, 2])
            self.wumpus -= 1
            self.label[i, j, 2] = None
            self.flags[i, j, 2] = False
            self.updateLabel(i, j)

    def shoot2(self):
        i, j = self.character.getIter()
        current = self.character.currentImage()
        self.character.shoot()
        if current == 0:
            j = j - 1
        elif current == 1:
            i = i + 1
        elif current == 2:
            i = i - 1
        elif current == 3:
            j = j + 1
        if self.isValid(i) and self.isValid(j):
            if self.label[i, j, 2]:
                killSprite(self.label[i, j, 2])
                self.wumpus -= 1
                self.label[i, j, 2] = None
                self.flags[i, j, 2] = False
                self.updateLabel(i, j)

    def updateLabel(self, x, y):
        adj = getAdj(x, y, self.size)
        for ar in adj:
            i, j = ar[:2]
            if self.label[i, j, 0]:
                wum = getAdj(i, j, self.size)
                haveWumpus = False
                for w in wum:
                    a, b = w[:2]
                    if self.label[a, b, 2]:
                        haveWumpus = True
                        break
                if haveWumpus:
                    continue
                else:
                    killSprite(self.label[i, j, 0])
                    self.label[i, j, 0] = None
                    self.flags[i, j, 0] = False

    def climbing_out(self):
        path = []
        x, y = self.character.getIter()
        while True:
            if x == self.start_x and y == self.start_y:
                break
            adj = getAdj(x, y, self.size)
            dis = []
            for a in adj:
                i, j = a[:2]
                if not self.explored[i, j]:
                    dis.append(self.size * 2)
                    continue
                had = False
                for p in path:
                    if p == [i, j]:
                        dis.append(self.size * 2)
                        had = True
                        break
                if not had:
                    dis.append(distance(a, [self.start_x, self.start_y]))
            id = np.argmin(dis)
            x, y = adj[id][:2]
            path.append([x, y])
        for p in path:
            x, y = p[:2]
            self.score.move()
            self.character.goto(x, y)
            tick(5)

    def gameOver(self):
        g = makeLabel('Game Over', 80, 80, 160, "Orange", "Showcard gothic", "clear")
        s = makeLabel('Score : '+str(self.score.point), 80, 80, 240, "Orange", "Showcard gothic", "clear")
        showLabel(g)
        showLabel(s)

    def isValid(self, i):
        if i < 0 or i > self.size - 1:
            return False
        return True


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def main():
    # Input
    size = 10
    agent_x = 0
    agent_y = 0
    pits = 5
    wumpus = 5
    gold = 10

    # Create map by input file

    flag, _, _, _, agent = inputMap('m1.txt')
    size = len(flag)
    game = TheWumpusWorld(size)
    label = createLabel(flag)

    # Create map by random

    #game = TheWumpusWorld(size)
    #label, flag, agent = create_random_map(size, pits, wumpus, gold)

    # Set up map
    agent_x, agent_y = agent
    game.addLabel(label, flag)
    game.setPositionAgent(agent_x, agent_y)

    # Output map
    #outputMap(flag, 'output_map.txt', [agent_x, agent_y])

    # Run AI

    PL(agent_x, agent_y, game)
    game.gameOver()
    endWait()

    while True:
        i, j = game.character.getIter()
        if isWumpus(game.flags[i, j]) or isPit(game.flags[i, j]):
            game.score.die()
            break
        if game.gold == 0 and game.wumpus == 0:
            break
        if keyPressed("up"):
            if game.character.Up():
                i, j = game.character.getIter()
                game.exploredRoom(i, j)
                game.score.move()
        elif keyPressed("down"):
            if game.character.Down():
                i, j = game.character.getIter()
                game.exploredRoom(i, j)
                game.score.move()
        elif keyPressed("right"):
            if game.character.Right():
                i, j = game.character.getIter()
                game.exploredRoom(i, j)
                game.score.move()
        elif keyPressed("left"):
            if game.character.Left():
                i, j = game.character.getIter()
                game.exploredRoom(i, j)
                game.score.move()
        elif keyPressed("space"):
            game.shoot2()
            game.score.shoot_arrow()
        elif keyPressed("a"):
            game.grabGold()
            game.score.pick_up_gold()
        tick(5)
    game.gameOver()
    endWait()


if __name__ == "__main__":
    main()







