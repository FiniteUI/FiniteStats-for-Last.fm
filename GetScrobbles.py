import requests
import sqlite3
import time
import math
import threading

api_key = '2250286cc9286ad20b304fc7650e63c3'
lfmhost = 'http://ws.audioscrobbler.com'
limit = 200
#dbUrl = 'C:/nodejsworkspace/workspace/StatCombiner/2.0/ScrobblesPy.db'
#dbUrl = 'D:\Documents\Programming Junk\Stat Combiner\2.0\ScrobbleDatabase.db'
dbUrl = 'ScrobbleDatabase.db'

selectDateSQL = 'select max(DateUTC) from Scrobbles where UserID = '
insertSQL = 'insert into Scrobbles(UserID, UserName, SongName, ArtistName, AlbumName, Date, DateUTC, DateCommitted) values(?,?,?,?,?,?,?,?)'
selectUserIdSQL = 'select max(UserID) from Scrobbles'
deleteAllSQL = 'delete from Scrobbles'
resetAutoincrementSQL = "delete from sqlite_sequence where name = 'Scrobbles'"

#returns one page of a users library
def getScrobblePage(user, page):
    url = lfmhost + '/2.0/?method=user.getRecentTracks&user=' + user + '&page=' + str(page) + '&limit=' + str(limit) + '&api_key=' + api_key + '&format=json'
    ScrobblePage = requests.get(url)
    pageData = ScrobblePage.json()
    return pageData
    #end getScrobblePage
    
#returns a user's scrobble count from their scrobbles page and not their user info
def getScrobbleCountFromScrobblePage(user):
    pageData = getScrobblePage(user, 1)
    scrobbleCount = pageData['recenttracks']['@attr']['total']
    return int(scrobbleCount)
    #end getScrobbleCountFromScrobblePage
    
#returns and open connection to the database, or none
def openDB():
    try:
        conn = sqlite3.connect(dbUrl)
        #print('Database opened...')
        return conn
    except Error as e:
        print(e)
    return None
    #end openDB

#closes the given database connection
def closeDB(conn):
    try:
        conn.close()
        #print("Database closed...")
    except Error as e:
        print(e)
    #end closeDB

#returns the date of the most recent scrobble for a specific user in the database
def getMostRecentUpdate(conn):
    cur = conn.cursor()
    cur.execute(selectDateSQL + str(userid))
    mostRecentUpdate = cur.fetchall()
    mostRecentUpdate = mostRecentUpdate[0][0]
    return mostRecentUpdate
    #end getMostRecentUpdate
    
#puts a scrobble(variables) into the database
def inputScrobble(conn, userid, username, song, artist, album, date, dateUTC):
    cur = conn.cursor()
    scrobble = (userid, username, song, artist, album, date, dateUTC, time.time())
    cur.execute(insertSQL, scrobble)
    conn.commit()
    #end inputScrobble
    
#puts a scrobble(list) into the database
def inputScrobble(conn, scrobble):
    cur = conn.cursor()
    cur.execute(insertSQL, scrobble)
    conn.commit()
    #end inputScrobble
    
#turns an array into a file, with special considerations for problematic characters, make better for CSV as well
def arrayToTextFile(array, filename):
    file = open(filename, 'w')
    for i in array:
        try:
            file.write(str(i))
        except UnicodeEncodeError as e:
            None
            '''
            for j in i:
                try:
                    file.write(str(j))
                except UnicodeEncodeError as e1:
                    None
            '''
        file.write('\n')
    file.close()
    #end arrayToTextFile
    
#inputs an array of scrobbles into the database
def inputArrayToDatabase(conn, array):
    cur = conn.cursor()
    cur.executemany(insertSQL, array)
    conn.commit()
    #end inputArrayToDatabase
    
#returns an array of a user's 'friends', or users they follow
def getUserFriends(username):
    url = lfmhost + '/2.0/?method=user.getfriends&user=' + username + '&api_key=' + api_key + '&format=json'
    friendData = requests.get(url).json()
    friends = []
    for i in friendData['friends']['user']:
        friends.append(i['name'])
    return friends
    #end getUserFriends
    
#gets the highest not used user id in the database
def getOpenUserID(conn):
    cur = conn.cursor()
    cur.execute(selectUserIdSQL)
    openID = cur.fetchall()
    openID = openID[0][0]
    openID += 1
    return openID
    #end getOpenUserId
    
#outdated, slower, has problems with accessing database sometimes, and doesn't account for scrobbles added while getting
#organizes and structures threads to input get all of a user's scrobbles and put them into the database in the threads
def inputAllScrobblesThreads(userid, username, threadCount):
    print('User: ' + username)
    scrobbleCount = getScrobbleCountFromScrobblePage(username)
    print('Scrobbles: ' + str(scrobbleCount))
    pageCount = math.ceil(scrobbleCount / limit)
    print('Pages: ' + str(pageCount))
    
    pagesPerThread = math.ceil(pageCount / threadCount)
    print('Threads: ' + str(threadCount))
    print('Pages per thread: ' + str(pagesPerThread))
    
    threads = []
    currentAssignedPagesCount = 0
    startTime = time.time()
    for i in range(0, threadCount):
        t = threading.Thread(target = inputPageRange, args = (userid, username, currentAssignedPagesCount + 1, currentAssignedPagesCount + pagesPerThread))
        currentAssignedPagesCount += pagesPerThread
        threads.append(t)
        t.start()
    while (threading.activeCount() != 0):
        None
    print('Done.')
    #end inputAllScrobblesThreads
    
#returns an array of scrobbles from a specified page range
def getPageRange(userid, username, scrobbleCountOriginal, start, stop, results, index):
    #startTime = time.time()
    scrobbleCount = scrobbleCountOriginal
    partialScrobbles = []
    for page in range(start, stop + 1):
        #print('Thread ' + threading.currentThread().getName() + ' page ' + str(page))
        currentPageData = getScrobblePage(username, page)
        #print(currentPageData)
        skip = 0
        """
        if (scrobbleCount < int(currentPageData['recenttracks']['@attr']['total'])):
            
            if (page != start):
                #print(threading.currentThread().getName() + ': Total scrobble count increased during get process, adjusting...')
                skip = int(currentPageData['recenttracks']['@attr']['total']) - scrobbleCount
            #print(threading.currentThread().getName() + ': skipping ' + str(skip))
            scrobbleCount = int(currentPageData['recenttracks']['@attr']['total'])
        """

        """
        if ('@attr' not in currentPageData['recenttracks']['track'][0]):
            currentlyScrobbling = 0
        else:
            currentlyScrobbling = 1
        """
        currentlyScrobbling = 0
            
        for scrobbleNumber in range(limit - 1 + currentlyScrobbling, - 1 + currentlyScrobbling + skip, -1):
            if ((page-1) * limit + scrobbleNumber + 1 - currentlyScrobbling <= scrobbleCount):
                scrobble = (
                    userid,
                    username,
                    currentPageData['recenttracks']['track'][scrobbleNumber]['name'],
                    currentPageData['recenttracks']['track'][scrobbleNumber]['artist']['#text'],
                    currentPageData['recenttracks']['track'][scrobbleNumber]['album']['#text'],
                    currentPageData['recenttracks']['track'][scrobbleNumber]['date']['#text'],
                    currentPageData['recenttracks']['track'][scrobbleNumber]['date']['uts'],
                    time.time() 
                    )
                partialScrobbles.append(scrobble)

    """
    #this gets the missing scrobble in case of total scrobble change
    #what if multiple scrobbles are added? need to do something in this case!! After that, should have 100% accuracy
        if (skip > 0):
            currentPageData = getScrobblePage(username, start)
            if ('@attr' not in currentPageData['recenttracks']['track'][0]):
                currentlyScrobbling = 0
            else:
                currentlyScrobbling = 1
            
            scrobble = (
                userid,
                username,
                currentPageData['recenttracks']['track'][0 + currentlyScrobbling]['name'],
                currentPageData['recenttracks']['track'][0 + currentlyScrobbling]['artist']['#text'],
                currentPageData['recenttracks']['track'][0 + currentlyScrobbling]['album']['#text'],
                currentPageData['recenttracks']['track'][0 + currentlyScrobbling]['date']['#text'],
                currentPageData['recenttracks']['track'][0 + currentlyScrobbling]['date']['uts'],
                time.time() 
                )
            #print('Getting missing scrobble ' + scrobble[2])
            partialScrobbles.append(scrobble)
    """
    
    results[index] = partialScrobbles
    #print(threading.currentThread().getName() + ' done')
    #endTime = time.time() - startTime
    #endTime = endTime
    #print('Thread ' + threading.currentThread().getName() + ' completed in ' + str(endTime) + ' seconds')
    #end getPageRange
    
#gets scrobbles from the added page if page count increases during the scrobble getiing process
def getAddedPage(username, userid):
    scrobbleCount = getScrobbleCountFromScrobblePage(username)
    pageCount = math.ceil(scrobbleCount / limit)
    currentPageData = getScrobblePage(username, pageCount)
    
    if ('@attr' not in currentPageData['recenttracks']['track'][0]):
        currentlyScrobbling = 0
    else:
        currentlyScrobbling = 1

    partialScrobbles = []
    for scrobbleNumber in range(limit - 1 + currentlyScrobbling, - 1 + currentlyScrobbling, -1):
        if ((pageCount-1) * limit + scrobbleNumber + 1 - currentlyScrobbling <= scrobbleCount):
            print(scrobbleNumber)
            scrobble = (
                userid,
                username,
                currentPageData['recenttracks']['track'][scrobbleNumber]['name'],
                currentPageData['recenttracks']['track'][scrobbleNumber]['artist']['#text'],
                currentPageData['recenttracks']['track'][scrobbleNumber]['album']['#text'],
                currentPageData['recenttracks']['track'][scrobbleNumber]['date']['#text'],
                currentPageData['recenttracks']['track'][scrobbleNumber]['date']['uts'],
                time.time() 
                )
            partialScrobbles.append(scrobble)            
    return partialScrobbles
    #end getAddedPage
    
#clears the database
def clearDatabase():
    conn = openDB()
    cur = conn.cursor()
    cur.execute(deleteAllSQL)
    cur.execute(resetAutoincrementSQL)
    conn.commit()
    closeDB(conn)
    #end of clearDatabase

#swaps two scrobbles in an array, for sorts
def swapScrobbles(array, a, b):
    temp = array[a]
    array[a] = array[b]
    array[b] = temp
    #end SwapScrobbles

#bubble sort for sorting the scrobble array by date
def bubbleSortScrobblesByDate(a, low, high):
    n = high + 1
    while (n != 0):
        newn = 0
        for i in range(low + 1, n):
            if (a[i - 1][6] > a[i][6]):
                swapScrobbles(a, i - 1, i)
                newn = i
        n = newn
    #end bubbleSortScrobblesByDate
    
def nestedIfSortScrobblesByDate(a, low, high):
    if (a[low][6] > a[low + 1][6]) and (a[low][6] > a[high][6]):
        if (a[low + 1][6] > a[high][6]):
            swapScrobbles(a, low, high)
        else:
            swapScrobbles(a, low, high)
            swapScrobbles(a, low + 1, low)
    elif (a[low + 1][6] > a[low][6]) and (a[low + 1][6] > a[high][6]):
        if (a[low][6] > a[high][6]):
            swapScrobbles(a, high, low)
            swapScrobbles(a, low + 1, high)
        else:
            swapScrobbles(a, low + 1, high)
    else:
        if (a[low][6] > a[low + 1][6]):
            swapScrobbles(a, low, low + 1)
    #end nestedIfSortScrobblesByDate
    
#quicksort, for sorting the scrobble array by date
def quickSortScrobblesByDate(a, low, high):
    if (low < high):
        if (high - low > 12):
            p = partitionScrobblesByDate(a, low, high)
            quickSortScrobblesByDate(a, low, p)
            quickSortScrobblesByDate(a, p + 1, high)
        elif (high - low > 3):
            bubbleSortScrobblesByDate(a, low, high)
        else:
            nestedIfSortScrobblesByDate(a, low, high)
    #end quickSortScrobblesByDate
        
#part of quicksort
def partitionScrobblesByDate(a, low, high):
    pivot = (low + high) // 2
    if (a[low][6] > a[pivot][6]):
        pivot = low
    if (a[high][6] < a[pivot][6]):
        pivot = high
    pivot = a[pivot][6]
    i = low - 1
    j = high + 1
    while (True):
        while(True):
            i = i + 1
            if (a[i][6] >= pivot):
                break
        
        while (True):
            j = j - 1
            if (a[j][6] <= pivot):
                break
        
        if (i >= j):
            return j
        
        swapScrobbles(a, i, j)
    #end partitionScrobblesByDate

#heapsort
#better array to text file
#compare heapsort and quicksort
#maybe synchorinized class and/or semaphores... bounded buffer type thing since get isn't very cpu intensive

#organizes and structures threads to input get all of a user's scrobbles and put them into the database
def inputAllScrobblesThreadsAtOnceSorted(userid, username, threadCount):
    print('User: ' + username)
    scrobbleCount = getScrobbleCountFromScrobblePage(username)
    print('Scrobbles: ' + str(scrobbleCount))
    pageCount = math.ceil(scrobbleCount / limit)
    print('Pages: ' + str(pageCount))
    
    pagesPerThread = math.floor(pageCount / threadCount)
    excessPages = pageCount % threadCount
    #print(excessPages)
    print('Threads: ' + str(threadCount))
    print('Pages per thread: ' + str(pagesPerThread))
    
    threads = []
    results = [None] * threadCount
    currentAssignedPagesCount = 0
    startTime = time.time()
    
    for i in range(0, threadCount):
        if (excessPages > 0):
            extraPage = 1
            excessPages -= 1
        else:
            extraPage = 0
        
        t = threading.Thread(target = getPageRange, args = (userid, username, scrobbleCount, currentAssignedPagesCount + 1, currentAssignedPagesCount + pagesPerThread + extraPage, results, i))
        currentAssignedPagesCount = currentAssignedPagesCount + pagesPerThread + extraPage
        threads.append(t)
        t.start()
    
    allScrobbles = []
    for t in threads:
        t.join()
    
    for i in range(threadCount):
        for j in results[i]:
            allScrobbles.append(j)

    """        
    #maybe what if a new page is made beacause of new scrobble? Deal with it here probably, also get all scrobbles array threads, and threadcount time test
    #instead of doing this check, to save time maybe add another flag that a thread can set when there is a page count change, try this for now though
    #check if pagecount changed
    #this method adds ~8% time
    scrobbleCount = getScrobbleCountFromScrobblePage(username)
    newPageCount = math.ceil(scrobbleCount / limit)
    if (newPageCount > pageCount):
        print('Page count change detected...')
        for i in range(pageCount + 1, newPageCount + 1):
            tempScrobbles = getAddedPage(username, userid)
            for j in tempScrobbles:
                allScrobbles.append(j)
    """
                

    endTime = time.time() - startTime
    print('Scrobbles gathered in ' + str(endTime) + ' seconds.')
    
    startTime = time.time()
    #print(allScrobbles)
    quickSortScrobblesByDate(allScrobbles, 0, len(allScrobbles) - 1)
    endTime = time.time() - startTime
    print('Scrobbles sorted in ' + str(endTime) + ' seconds.')
    print(len(allScrobbles))
    startTime = time.time()
    conn = openDB()
    inputArrayToDatabase(conn, allScrobbles)
    closeDB(conn)
    endTime = time.time() - startTime
    print('Scrobbles committed to database in ' + str(endTime) + ' seconds.')
    print('Done.')
    #end inputAllScrobblesThreadsAtOnce
    
'-------------------------------------------------------------------------------------------------------------------------------------------------------------------'

clearDatabase()
inputAllScrobblesThreadsAtOnceSorted(2, 'Darian_pennick', 32)
