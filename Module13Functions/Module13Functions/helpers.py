#codelab by Ali Mustafa 
#visit http://ialimustafa.com for more information
#copyright@2018
#Dont Redistribute without Cedits

def getNames():
    names = ['Ali Mustafa', 'Saurabh', 'Danny']
    newName = input('Enter last guest: ')
    names.append(newName)
    return names

def printNames(names):
    for name in names:
        print(name)
    return