"""Print structured point-program head events for generation and admission."""

def structured_tool_pair(call, event):
    if call['call_id'] != event['call_id'] or call['name'] != event['name']:
        raise ValueError('mismatched_tool_response')
    args, name = call['arguments'], call['name']
    def value(v, places=2):
        if isinstance(v, list): return '(' + ', '.join(value(x, places) for x in v) + ')'
        return f'{v:.{places}f}' if isinstance(v, (int, float)) else str(v)
    e = event
    get = lambda key: value(e['values'][e['call_id']+'.'+key]['value'])
    parts = []
    if name == "depth_at":
        import json
        k = args.get("image_frame", args["frame"])
        image = f" image_frame={k}" if "image_frame" in args else ""
        pts = json.dumps(args["pts"], separators=(",", ":"))
        parts.append(f"<depth_at frame={args['frame']}{image} pts={pts}>")
        parts.append("\n".join(p["line"] for p in e["points"]))
    elif name == "pose":
        k = args["frame"]
        parts.append(f"<pose frame={k}>")
        parts.append(f"gives f1 centre {get('t')} m ({e['call_id']}.t), "
                        f"camera-to-f1 matrix {get('R')} ({e['call_id']}.R), and "
                        f"L_{k}-to-f1 matrix {get('level_R')} ({e['call_id']}.level_R); "
                        f"yaw {value(e['values'][e['call_id']+'.yaw']['value'], 0)} degrees ({e['call_id']}.yaw), positive to the left.")
    elif name == "move":
        parts.append(f"<move from={args['from']} to={args['to']}>")
        delta = e["values"][e["call_id"]+".delta"]["value"]
        parts.append(f"dx = {delta[0]:+.2f} m, dy = {delta[1]:+.2f} m, dz = {delta[2]:+.2f} m, "
                        f"distance = {get('distance')} m (L_{args['from']}, dy positive down; "
                        f"{e['call_id']}.delta; {e['call_id']}.distance).")
    else: raise ValueError("unbacked_tool: " + str(name))
    return tuple(parts)
