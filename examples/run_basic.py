from launcher import Simulator

if __name__ == "__main__":
    sim = Simulator(num_nodes=20, packet_interval=10, transmission_mode="Random")
    sim.run(500)
    print(sim.get_metrics())
