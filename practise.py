class weird():
    def __init__(self,x,y):
        
        self.y=y
        self.x=x

    def getX(self):
        
        return self.x

    def getY(self):
        return self.y

w1 =weird(x=7,y=8)
print(w1.getX())
