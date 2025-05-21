# Fortnite Archives (maps, locations) since the beginning of the game until now

This projects gives you access to every map in .jpg & every cities per map version (in JSON).\
This may have errors, since I've mainly parsed & scraped wikis or websites that appromatively gave what I needed. It has been hard to retrieve all datas and I'm working on doing it better, if you have advices or recommandations, don't mind telling me.\
This project can be used to build, per example, an interactive map for a particular (or current) season (using Leaflet), with cities and good quality image of the map.\
Don't be confused by the folders names (in Chapters folders), Saison is equal to Season (you probably guessed it). I've named them in French by mistake (will be corrected).\\

## Formats, extensions for images of maps

All maps have been named after the season corresponding to it.\
All of them are avalaible in "jpg".\
Depending on the age of the season, the map may be in 1024x1024, 2048x2048 or 4096x4096 (usually (almost all of them) 2048x2048).\

## About JSONs and cities

I've worked on a way to scrap (that's what i did for all the .jpg maps), and retrieve every cities name for each season by using an endpoint from fandom.wiki for Fortnite,\
The correct folder structure that I am using, would be :
- Chapter 6/
- - Season 4/
- - -  36.00/
- - - - 36.00.json
- - - - 36.00.jpg
- - -  36.10/
- - - - 36.10.json
- - - - 36.10.jpg
- - -  36.20/
- - - - 36.20.json
- - - - 36.20.jpg

Every season (or more precisely every update) will claim his own folder, and this folder will contain the map (jpg) and the cities corresponding to the map version (json).\

## I'd like to go even deeper in my work

If anyone like the projects, let me know or give a star. If the projects is helpful and interesting for many people, I'll work on every weapons from every season in the same way i did for maps and cities.\

## This is of course free to use :)

