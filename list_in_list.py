airline_details=[["AI",8], ["EM",10],["BA",7]]

#To get the details of Emirates (EM) airline
#Prints a list
print(airline_details[1])

#To get the number of flights operated by British Airways (BA)
#[2][1] refers to 2nd list and 1st value, inside airline_details
#Remember counting is 0 based
print(airline_details[2][1])

#To display the details of all airlines
print("Airline details as a list:")
for airline in airline_details:
    print(airline)

#To display the number of flights operated by each airline
print("No. of flights operated by each airline:")
for airline in airline_details:
        print(airline[1])