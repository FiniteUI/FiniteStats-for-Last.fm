//imports
const http = require('http');
const sql = require('sqlite3').verbose();

//constants
const api_key = '';
const lfmhost = 'ws.audioscrobbler.com';
const lfmport = 80;
const limit = 75;
const dbUrl = 'C:/Users/Trey/Documents/SQLiteStudio/FSDB1.db';

//variables
var username = '';
var userid = 1;
var pageCount = 0;
var db;
var stmt;
var selectDateSQL = 'select max(DateUTC) from Scrobbles where UserID = ';
var temp = [];
var total = 0;
var mostRecentUpdate;
var startTime;

//returns one page of scrobbles in the callback
getScrobblePage = function(user, page, cb) {
	try {
		http.get({
			host: lfmhost,
			port: lfmport,
			path: '/2.0/?method=user.getRecentTracks&user=' + user + '&page=' + page + '&limit=' + limit + '&api_key=' + api_key + '&format=json'
		},
		res => {
			res.setEncoding("utf8");
			let body = "";
			res.on("data", data => {
				body += data;
			});//end res.on data
			res.on("end", () => {
				body = JSON.parse(body);
				cb(body);
			});//end res.on end
		});//end http.get
	}//end try
	catch(e) {
		console.log(e);
	}//end catch
};//end getScrobbles

//gets the page count and calls openDB
function getPageCount() {
	getScrobblePage(username, 1, function(x) {
		pageCount = x.recenttracks["@attr"].totalPages;
		console.log('Page count: ' + pageCount);
		total = x.recenttracks["@attr"].total;
		console.log('Total scrobbles: ' + total);
		openDB();
		});
};//end getPageCount

//opens the DB, calls getMostRecentUpdate, calls Insert
function openDB() {
	db = new sql.Database(dbUrl, (err) => {
		  if (err) {
		    return console.error(err.message);
		  }
		  getMostRecentUpdate(function (x) {
			  mostRecentUpdate = x;
			  console.log(mostRecentUpdate);
			  //insert(pageCount);
			  insert(1);
		  });
		});
};//end openDB

//gets the most recent scrobble of this user in the database
function getMostRecentUpdate(cb) {
	db.get(selectDateSQL + userid, [], (err, row) => {
		  if (err) {
			  console.error(err.message);
		  }
		  if (row != undefined) {
			  cb(row['max(DateUTC)']);
		  }//end if
		  else {
			 cb(undefined); 
		  };//end else
		});
};//end getMostRecentUpdate

//inserts the scrobbles from a page into the database
function insert(p) {
	getScrobblePage(username, p, function(x) {
		for (var j = limit-1; j > -1; j--) {
				if ((p-1) * limit + j <= total) {
					if (x.recenttracks.track[j]['@attr'] == undefined) {
						if (x.recenttracks.track[j].date['uts'] > mostRecentUpdate) {
							temp = [];
							temp.push(userid);
							temp.push(username);
							temp.push(x.recenttracks.track[j].name);
							temp.push(x.recenttracks.track[j].artist['#text']);
							temp.push(x.recenttracks.track[j].album['#text']);
							temp.push(x.recenttracks.track[j].date['#text']);
							temp.push(x.recenttracks.track[j].date['uts']);
							temp.push(Date.now());
							stmt = db.prepare(`INSERT INTO Scrobbles(UserID, UserName, SongName, ArtistName, AlbumName, Date, DateUTC, DateCommitted) VALUES(?,?,?,?,?,?,?,?)`, temp)
							try {
								stmt.run();
								stmt.finalize(console.log('Page ' + p + ' number ' + j + ' committed at ' + Date.now()));//make a way to report this page by page
							}
							catch(e) {
								console.log(e);
								Console.log('Page ' + p + ' number ' + j + ' trying again...');
								j++;
							};
						}//end if
						else {
							console.log('Page ' + p + ' committed');
							p = pageCount + 1;
							break;
						};//end else
					};//end if
				};//end if	
		};//end for
		if (p < pageCount) {
			insert(p+1);
		}
		//last recursive call
		else if (p >= pageCount) {
			closeDB();
		};
	});//end GS CB
};//end insert

//closes the database
function closeDB() {
	db.close();
	console.log('Success!');
	console.log('Completed in ' + (Date.now() - startTime) + ' milliseconds');
};//end closeDB

//the whole shebang, calls getPageCount
function grabScrobbles(uName, UID) {
	startTime = Date.now();
	userid = UID;
	username = uName;
	getPageCount();
};//end run

//do the stuff, for now
grabScrobbles('bigwill817', 1);
