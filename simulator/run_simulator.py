from simulator.runtime import AquaponicsSimulator


if __name__ == "__main__":
    # 中文注释：仅保留调试入口；正常运行时模拟器随 Flask 主站启动。
    AquaponicsSimulator().run()
