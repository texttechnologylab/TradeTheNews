from datetime import timedelta

STARTING_DEPOT_VOLUME = 10000

# HoldDuration in Minutes, NameOfStrategie
TRAINDING_STRATEGIES = [
    (300, "linear"),
    (300, "exponential3"),
    (300, "exploding")
]

COLORS = ["#336600", "#996600", "#cc0099"]


def trading_strategies(score, time):
    '''
    This function implements the different Trading strategies
    YOU ALSO CAN IMPLEMENT YOUR OWN
    '''
    lists_to_return = [time]
    lists_to_return_sell = []
    for hold_duration, strategie in TRAINDING_STRATEGIES:
        if strategie == TRAINDING_STRATEGIES[0][1]: # linear 
            stock_to_buy = score
        elif strategie == TRAINDING_STRATEGIES[1][1]: # exponential3
            stock_to_buy = score**3
        elif strategie == TRAINDING_STRATEGIES[2][1]: # exploding
            stock_to_buy = score* (1.1 ** (score**2))
        else:
            continue
        lists_to_return.append((strategie, stock_to_buy))
        lists_to_return_sell.append([time + timedelta(minutes=hold_duration), (strategie, -stock_to_buy)])
    lists_to_return = [lists_to_return]
    lists_to_return.extend(lists_to_return_sell)
    return lists_to_return

