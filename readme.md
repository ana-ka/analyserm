# analyzerm
## some crude python tools

readmore.de is a German website dedicated to e-sports coverage.
These tools were created many years ago out of curiosity to extract some information about the readmore user base and community structure. They might not work anymore by the time of this commit.


### usage:
* id_to_name.py - scrape profile information
* analyzerm.py - create gephi format graphs from gathered information
* communi.py - stand alone tool to create community graphs with a certain user as the starting node

### notes:
* adjust parameters as needed in the source
* this implementation depends on Pysocks
* scripts are set up to use tor
