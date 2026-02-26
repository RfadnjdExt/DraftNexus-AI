import json
import subprocess
import os

json_path = 'android/core/data/src/main/assets/heroes.json'
pb_path = 'android/core/data/src/main/assets/heroes.pb'
proto_dir = 'android/core/model/src/main/proto'
proto_file = 'android/core/model/src/main/proto/com/draftnexus/ai/core/model/hero.proto'

with open(json_path, 'r') as f:
    heroes = json.load(f)

textpb_path = 'android/core/data/src/main/assets/wrapped_heroes.textpb'

with open(textpb_path, 'w') as f:
    for h in heroes:
        f.write("heroes {\n")
        f.write(f"  id: {h['id']}\n")
        f.write(f"  name: \"{h['name'].replace('\"', '\\\"')}\"\n")
        f.write(f"  primary_lane: {h['primaryLane']}\n")
        f.write(f"  secondary_lane: {h['secondaryLane']}\n")
        f.write(f"  icon_url: \"{h['iconUrl']}\"\n")
        in_logs = str(h.get("inRealLogs", True)).lower()
        f.write(f"  in_real_logs: {in_logs}\n")
        for s in h["stats"]:
            f.write(f"  stats: {s}\n")
        f.write("}\n")

print("Running protoc...")
# Use protoc to encode
with open(textpb_path, 'r') as stdin_f, open(pb_path, 'wb') as stdout_f:
    result = subprocess.run(
        ['protoc', '--encode=com.draftnexus.ai.core.model.HeroListProto', f'-I={proto_dir}', proto_file],
        stdin=stdin_f,
        stdout=stdout_f,
        stderr=subprocess.PIPE
    )

if result.returncode != 0:
    print(f"Error: {result.stderr.decode()}")
    os.remove(pb_path)
else:
    print(f"Successfully generated {pb_path}")
    os.remove(textpb_path)
