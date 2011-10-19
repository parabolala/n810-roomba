
def pick_one(selection, prompt):
    if len(selection) > 1:
        print prompt
        for i, port in enumerate(selection):
            print i, port
        port_num = raw_input('[0]> ')
        try:
            port_num = int(port_num)
            if not 0 <= port_num < len(selection):
                raise ValueError
        except ValueError:
            port_num = 0
            print 'Using 0: %s' % selection[port_num]
        res = selection[port_num]
    elif not selection:
        raise SystemExit()
    else:
        res = selection[0]
    return res

