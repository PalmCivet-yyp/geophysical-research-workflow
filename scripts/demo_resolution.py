#!/usr/bin/env python3
"""Illustrative 1D Gaussian-blur synthetic demo; NOT a geophysical forward/inverse model."""
import argparse
import csv
import json
import math
import random
from pathlib import Path


def profile(coords, shape):
    if shape == "sharp":
        return [0.5 if x >= 0 else -0.5 for x in coords]
    if shape == "ramp":
        return [max(-0.5,min(0.5,x/3.0)) for x in coords]
    raise ValueError(shape)


def smooth(values, spacing=0.1, sigma=1.0):
    offsets=range(-40,41)
    weights=[math.exp(-0.5*(k*spacing/sigma)**2) for k in offsets]
    out=[]
    for i in range(len(values)):
        v=sum(values[min(len(values)-1,max(0,i+k))]*w for k,w in zip(offsets,weights))
        out.append(v/sum(weights))
    return out


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    coords=[-4+0.1*i for i in range(81)]
    sharp=smooth(profile(coords,"sharp"))
    ramp=smooth(profile(coords,"ramp"))
    rng=random.Random(137)
    observed=[s+rng.gauss(0,0.02) for s in sharp]
    def rms(x,y):return math.sqrt(sum((a-b)**2 for a,b in zip(x,y))/len(x))
    with (out/"synthetic_profiles.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["x_arbitrary_units","blurred_sharp_arbitrary_units","blurred_ramp_arbitrary_units","toy_observation_arbitrary_units"])
        for values in zip(coords,sharp,ramp,observed):w.writerow([f"{v:.6f}" for v in values])
    metrics={
      "demo_type":"illustrative_1D_gaussian_blur_not_physical_forward_model",
      "data_origin":"synthetic_only",
      "seed":137,
      "x_domain_arbitrary_units":[-4,4],
      "grid_interval_arbitrary_units":0.1,
      "blur_sigma_arbitrary_units":1.0,
      "random_noise_sigma_arbitrary_units":0.02,
      "rms_sharp_to_synthetic_observation":rms(sharp,observed),
      "rms_ramp_to_synthetic_observation":rms(ramp,observed),
      "scientific_decision":"NOT_ASSESSED",
      "warning":"Not a gravity calculation, inversion, preregistered recovery benchmark, or evidence of any real geological boundary."
    }
    (out/"demo_metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Synthetic-only demo written to {out}. No geophysical detection claim.")
    return metrics


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=Path("toy-output"))
    a=p.parse_args()
    run(a.output)
