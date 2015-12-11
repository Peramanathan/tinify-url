# Tinify
For the given url it will tinify the url and return the tinified url

### Tasks and Requirements
The assignment is to use Python and a web framework to create a URL shortener similar to `http://bit.ly​`, but with a different URL encoding scheme. The shortened URLs will have the form `http://myurlshortener.com/​<word>/` where 
`<word>`` is a word from the english language. 

- [x] Make sure to fulfill all the requirements stated in this document. 
- [x] You must use Python to complete this assignment. You may use any frameworks and libraries you want to. 
- [x] Focus on writing clean, good looking and easily understandable code.  
- [x] At Fyndiq it is more important to write robust, easily readable and correct code than to do 
it quickly, so please pay attention to detail and corner cases. 
- [x] Provide a README with instructions on how to install and run the code in a contained environment, assuming that the computer that is to run the assignment does not have any frameworks or libraries installed. 
- [x] Use sqlite for database, and you could attach the database file with the finished code so that it is easier to run it. 
- [x] Make tests (unit tests and/or integration tests) for your code.


### Running the app
 
1. `git clone https://github.com/Peramanathan/tinify-url.git`
2. `cd tiny-url`
4. `virtualenv tinyurl-env`   [`sudo pip install virtualenv` if virtualenv not installed before]
5. `source tinyurl-env/bin/activate`
5. `pip install -r requirements.txt`  [one time only]
6. `python app.py`
4. Open `localhost:5000` in browser