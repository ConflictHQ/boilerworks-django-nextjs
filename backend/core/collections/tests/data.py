days = 'A Sun', 'B Mon', 'C Tue', 'D Wed', 'E Thu', 'F Fri', 'G Sat'
days_number = [
    (days[(day + 2) % 7], day)
    for day in range(31)
]
