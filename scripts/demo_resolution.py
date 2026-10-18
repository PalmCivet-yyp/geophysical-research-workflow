#!/usr/bin/env python3
"""抽象一维高斯平滑合成演示（不是真实地球物理正演/反演）。

目的：制造可重复的数据与指标文件，演示“模型差异、噪声、结果存档”的概念。
坐标、振幅和模糊尺度都使用任意单位，不能据此对真实地质边界作出判断。
"""
import argparse
import csv
import json
import math
import random
from pathlib import Path


def profile(coords, shape):
    """按给定坐标生成两类理想1D输入信号：阶跃 sharp 或线性过渡 ramp。

    这两个信号是用于演示的数学形状，不等价于地下密度/速度异常模型。
    未知形状将抛出ValueError，避免静默回退到某个默认假设。
    """
    if shape == "sharp":
        return [0.5 if x >= 0 else -0.5 for x in coords]
    if shape == "ramp":
        return [max(-0.5,min(0.5,x/3.0)) for x in coords]
    raise ValueError(shape)


def smooth(values, spacing=0.1, sigma=1.0):
    """用固定截断范围内的高斯权重平滑一维信号。

    边缘采用端点值延拓，避免访问数组界外；每点按权重和归一化。
    sigma是抽象坐标单位下的平滑尺度，不代表仪器真实分辨率。
    """
    # [-40, 40]的离散窗口与0.1网格步长对应，演示而非物理核函数。
    offsets=range(-40,41)
    weights=[math.exp(-0.5*(k*spacing/sigma)**2) for k in offsets]
    out=[]
    for i in range(len(values)):
        v=sum(values[min(len(values)-1,max(0,i+k))]*w for k,w in zip(offsets,weights))
        out.append(v/sum(weights))
    return out


def run(out):
    """输出可重复的合成CSV和JSON指标，返回指标字典。

    固定随机种子137可保证相同环境下生成同样的噪声序列；
    科学结论标记固定为NOT_ASSESSED，防止演示被误认成识别性检验。
    """
    out.mkdir(parents=True, exist_ok=True)
    coords=[-4+0.1*i for i in range(81)]
    sharp=smooth(profile(coords,"sharp"))
    ramp=smooth(profile(coords,"ramp"))
    # 与全局random状态隔离：运行该函数不依赖外部脚本使用随机数的顺序。
    rng=random.Random(137)
    observed=[s+rng.gauss(0,0.02) for s in sharp]
    # 仅计算两个示例信号间的均方根差，不用于地质模型优劣的科学判决。
    def rms(x,y):
        """计算两组同长度示例信号的RMS差（任意单位）。"""
        return math.sqrt(sum((a-b)**2 for a,b in zip(x,y))/len(x))
    with (out/"synthetic_profiles.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["x_arbitrary_units","blurred_sharp_arbitrary_units","blurred_ramp_arbitrary_units","toy_observation_arbitrary_units"])
        for values in zip(coords,sharp,ramp,observed):w.writerow([f"{v:.6f}" for v in values])
    # JSON同时保存随机种子、网格、噪声参数与解释边界，便于后续溯源。
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


# 从命令行运行时，默认创建toy-output目录；公开仓库内应使用--output指定外部目录。
if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=Path("toy-output"))
    a=p.parse_args()
    run(a.output)
