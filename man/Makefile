shairport-sync.1: shairport-sync.1.xml
	xmltoman shairport-sync.1.xml > shairport-sync.1

shairport-sync.html: shairport-sync.1.xml
	xsltproc xmltoman.xsl shairport-sync.1.xml > shairport-sync.html

all: shairport-sync.1 shairport-sync.html

clean:
	rm shairport-sync.1
	rm shairport-sync.html
