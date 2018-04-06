# FiniteStats-for-Last.fm
This is the start of a personal to make a web application for analyzing and manipulating data for a user from Last.fm's web API.

I've worked on this off and on throughout my Spring 2018 semester.

Last.fm is a website that tracks a users music listening habits so that they can look at their statistics. My eventual plan for this project is for it to be a web application for advanced manipulation and examination of Last.fm statistics.

Note: On Last.fm, a "Scrobble" is a listen or a play of a specific song.

This is just the basic start of this project. Originally I thought it would be neccessary to first get a User's scrobbles and add them to a local database, however I've recently been rethinking that.

AddMyStuffToDB.js is my first attempt at this, and my first experience writing in JavaScript. It just grabs a user's scrobbles and adds them to a local database, however it is very slow and does not account for anomalies like scrobbles added after the get process has begun.

GetScrobbles.py is the current version written in python, which contains many methods that do a number of different things. I left all outdated and test methods in instead of overwriting them when I made a better version, so the code towards the top tends to be older, and generally worse.

First I tried getting all the scrobbles and inputting them into the database one at a time, but that was a very slow process that took several hours. (My Last.fm account which I used for testing has about 65,000 scrobbles) Then I tried putting a page into the database at a time and realized this was faster, eventually getting all the scrobbles to an array and inputting them into a database all at once. This took the process down from several hours to about 170 seconds on average. Later I added threads and used them each to get a page range and then put that data into the database. After testing with different thread counts to find the ideal amount, I concluded that about 32 threads yielded the best performance, at about 15 seconds for the whole process, much better than several hours.

There are also methods for storing scrobbles in a textfile, and sorting them by date (due to the fact that using threads means they are gotten out of order).

Later I added support for Scrobbles added after the get process has started, which posed some interesting challenges due to Last.fm's odd way of storing songs that are currently being listened to (listed below). I also added support for when an added scrobble is enough to add an extra page of scrobbles.

With the Last.fm API, the maximum amount of scrobbles you can retrieve on one page is 200. They are numbered 0 - 199. However, if a user is currently listening to music, the song that they are currently listening to is (for some reason) put in spot 0 of every single page, so if a user is currently listening to music you need to grab not spots 0 - 199, but spots 1 - 200. Also, these currently playing songs have different attribute lists than ones not currently playing, so if your program doesn't recognize this and tries to access these as normal scrobbles, it is likely to crash.

A lot of this program is unneccesary and just for fun. I enjoyed seeing how accurate and efficient I could be.
