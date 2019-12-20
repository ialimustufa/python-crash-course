students=[]
temp=[]
for i in range(0,2):
  temp.append(input("Enter Student Name"))
  temp.append(int(input("Enter marks of subject 1:")))
  temp.append(int(input("Enter marks of subject 2:")))
  students.insert(i,temp[0:3])
  temp.clear()
print(students)