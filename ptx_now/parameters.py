
path_profiles = r'/run/user/1000/gvfs/smb-share:server=iipsrv-file3.iip.kit.edu,share=ssbackup/weatherOut/weatherOut_Uwe/'
path_local = '/home/localadmin/Dokumente/ptx_robust_data/'

costs_missing = 3.75

electricity_available = True
electricity_price = 10

demand_type = 'total'
energy_carrier = 'FT'

countries = ['Saudi Arabia', 'Chile', 'Germany', 'Kazakhstan']
# countries = ['Australia']

# Chile + Saudi Arabia in 168

if energy_carrier == 'FT':
    framework_name = 'FT_all_data_no_scaling.yaml'  # 'hydrogen_all_data_no.yaml'
elif energy_carrier == 'Hydrogen':
    framework_name = 'hydrogen_all_data_no.yaml'
else:
    framework_name = 'MeOH.yaml'

cluster_length = 336
# cluster_lengths = [336, 312, 288, 264, 240, 216, 192, 168, 144, 120]
cluster_lengths = [8760]
# cluster_lengths = [24, 48, 72, 96, 120, 144, 168, 192, 216, 240, 264, 288, 312, 336, 8760]
