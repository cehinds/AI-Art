"""Rebuild the 23 retained cavern object view sets from raw atlases, offline."""
from build_batch import process
BATCHES = [
 ('raw/caverns-walls-entrance.png',[('caverns-cave-wall-straight','Cave wall straight'),('caverns-cave-wall-corner','Cave wall corner'),('caverns-cave-wall-endcap','Cave wall endcap'),('caverns-cave-entrance-arch','Cave entrance arch')]),
 ('raw/caverns-ramp-formations-columns.png',[('caverns-cave-rock-ramp','Cave rock ramp'),('caverns-stalagmite','Stalagmite'),('caverns-stalactite-hanging','Stalactite hanging'),('caverns-stone-column','Stone column')]),
 ('raw/caverns-crystal-wall-clusters.png',[('caverns-crystal-wall','Crystal wall'),('caverns-red-crystal-cluster','Red crystal cluster'),('caverns-blue-crystal-cluster','Blue crystal cluster'),('caverns-green-crystal-cluster','Green crystal cluster')]),
 ('raw/caverns-water-tiles.png',[('caverns-underground-lake-edge','Underground lake edge'),('caverns-underground-lake-corner','Underground lake corner'),('caverns-cave-stream','Cave stream')]),
 ('raw/caverns-mine-rails-cart.png',[('caverns-mine-rail-straight','Mine rail straight'),('caverns-mine-rail-curve','Mine rail curve'),('caverns-mine-rail-junction','Mine rail junction'),('caverns-mine-cart','Mine cart')]),
 ('raw/caverns-support-lift-mushroom-ruin.png',[('caverns-timber-mine-support','Timber mine support'),('caverns-cave-lift-platform','Cave lift platform'),('caverns-giant-cave-mushroom','Giant cave mushroom'),('caverns-underground-ruin-doorway','Underground ruin doorway')]),
]
if __name__ == '__main__':
 for raw,objects in BATCHES: process(raw,objects)
