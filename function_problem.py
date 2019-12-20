#PF-Exer-7

def calculate_total_ticket_cost(no_of_adults, no_of_children):
    total_ticket_cost=0
    rate_for_adult=37550.0
    rate_for_child=(1/3)*rate_for_adult
    service_tax=1.07
    holiday_discount=0.1
    
    
    total_ticket_cost=(no_of_adults*rate_for_adult)+(no_of_children*(rate_for_child))
    total_ticket_cost*=service_tax
    total_ticket_cost*=holiday_discount

    return total_ticket_cost


#Provide different values for no_of_adults, no_of_children and test your program
total_ticket_cost=calculate_total_ticket_cost(5,2)
print("Total Ticket Cost:",total_ticket_cost)