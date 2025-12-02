import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

df = pd.read_csv("Data/g05_sp3_interp_30s.csv")

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

ax.plot(df["X_m"], df["Y_m"], df["Z_m"], color="red", linewidth=1.0)

ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.set_zlabel("Z (m)")
ax.set_title("3D Orbit of G05 from interpolated SP3 (30 s)")

plt.tight_layout()
plt.savefig("G05_SP3_orbit_3d.png", dpi=300)
plt.show()
