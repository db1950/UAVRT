import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

def GatherData(tlog_text, AltOutput, LatLonOutput, AntDataFile, FinalOutputFile ):

    def CheckFlightMode(splice, FlightInit):
        ''' Returns true if the UAV is currently in flight, false if stationary
        This function is intended for the FlightInit variable which is used to indicate whether the UAV is in flight
        or not. By testing to see whether the existing flight is'''
        if len(splice) > 10:
            if splice[10] == "0":
                if splice[21] == "4":
                    return True
                if splice[21] == "3":
                    return False
            else:
                if FlightInit == True:
                    return True
                else:
                    return False

    LocAltData = ''
    AltData = []
    CompassData = []
    LatLonData = ''
    LatLonAvg = []       # Time, Lat, Lon, 2-Dimensional
    points = 0           # the number of data points for Lat and Lon. Used for averaging.
    FinalData = ''
    reset_alt = False   # used to ensure that the altitude data collected is relative to the start of the measurement position
    alt_Flag = False    # Used to add the latitude and longitude to the New Flight flag
    FlightNum = 0

    FlightInit = False  # A variable used to determine whether or not a flight has been initiated
    file = open(tlog_text, 'r', encoding = 'UTF-8')
    # The generated tlogs will use encoding that is unreadable by Python's normal ASCII encoding. It must be reworked.

    for line in file:
        splice = line.split()
        FlightInit = CheckFlightMode(splice, FlightInit)
        if FlightInit:
            if len(splice) > 10:
                # Used to handle random array size errors
                if (splice[10] == "4A") or (splice[10] == "18"):
                    # Code for obtaining data calculated for the user interface in MissionPlanner
                    if (splice[2] == "PM") and splice[1][0:1] != "12":
                        splice[1] = ''.join(((str(int(splice[1][0:1])+12)), ":", splice[1][2:], " "))
                    # Conversion to military time
                        if splice[10] == "18":
                            current = len(LatLonAvg)
                            if current == 0:
                                LatLonAvg.insert(current, [splice[1], float(splice[15]), float(splice[17])])
                                current += 1
                                points += 1

                            elif LatLonAvg[current - 1][0] == splice[1]:
                                points += 1
                                prev = current -1
                                LatLonAvg[prev][1] = (LatLonAvg[prev][1] + float(splice[15]))
                                LatLonAvg[prev][2] = (LatLonAvg[prev][2] + float(splice[17]))
                            else:
                                prev = current - 1
                                LatLonAvg[prev][1] = str(LatLonAvg[prev][1]/(points*1*10**7))
                                LatLonAvg[prev][2] = str(LatLonAvg[prev][2]/(points*1*10**7))
                                LatLonAvg.insert(current, [splice[1], float(splice[15]), float(splice[17])])
                                if alt_Flag == True:
                                    alt_Flag = False
                                    split_spot = ''.join(('Flight Plan ', str(FlightNum)))
                                    spliceLocAlt = LocAltData.split(split_spot)
                                    LocAltData = ''.join((spliceLocAlt[0], split_spot, ' lat/lon: ',
                                                    LatLonAvg[prev][1], ' ', LatLonAvg[prev][2], spliceLocAlt[1]))
                                LatLonData = ''.join((LatLonData, LatLonAvg[prev][0], ' ', str(LatLonAvg[prev][1]), ' ', str(LatLonAvg[prev][2]), '\n'))
                                current += 1
                                points = 1
                          ###  LatLonData = ''.join((LatLonData, splice[1], ' ', splice[15], ' ', splice[17], '\n'))
                        if splice[10] == "4A":
                            Alt = float(splice[-10])*3.28084
                        # Conversion from meters to feet
                            if LocAltData == "" or reset_alt:
                                HomeAlt = Alt
                                FlightNum += 1
                                LocAltData = ''.join((LocAltData, 'Flight Plan ', str(FlightNum), '\n'))
                                reset_alt = False
                                alt_Flag = True
                                altloc_insert = len(LocAltData)
                            LocAltData = ''.join((LocAltData, "time ", splice[1], "heading ", splice[-6], " alt_amsl ", str(Alt), " alt_rel ", str(Alt - HomeAlt),  '\n'))
                            AltData.append(Alt)
                            CompassData.append(splice[-6])
        else:
            reset_alt = True


    file.close()

    x = LocAltData.split('\n')
    y = LatLonData.split('\n')
    index = 0
    NewData = ''

# Adding in the GPS Data where applicable
    for each in x:
        x2 = each.split(' ')
        if index < len(y):
            if x2[0] != 'Flight':
                LocAltInt = 3600*int(x2[1][0:2]) + 60*int(x2[1][3:5]) + int(x2[1][6:8])
                if y[index] != '':
                    LatLonInt = 3600*int(y[index][0:2]) + 60*int(y[index][3:5]) + int(y[index][6:8])
                if x2[1] == y[index][0:8]:
                    NewData = ''.join((NewData, each, ' lat/lon ', (y[index][8:]), '\n'))
                if LatLonInt < LocAltInt:
                    index += 1
                    NewData = ''.join((NewData, each, ' lat/lon None Recorded \n'))
                    if index < len(y):
                        if x2[1] == y[index][0:8]:
                            NewData = ''.join((NewData, each, ' lat/lon ', (y[index][8:]), '\n'))
                else:
                    NewData = ''.join((NewData, each, ' lat/lon None Recorded \n'))
            else:
                NewData = ''.join((NewData, each, '\n'))
                # In the case of multiple flights during one tlog, flight dividers are necessary.

    #print(NewData)

    file = open(AltOutput, 'w')
    file.write("time HH:MM:SS heading (°) alt_amsl (ft) alt_rel (ft)   lat             lon \n")
    file.write(LocAltData)
    file.close()

    file = open(LatLonOutput, 'w')
    file.write("time HH:MM:SS heading (°) alt_amsl (ft) alt_rel (ft)   lat             lon \n")
    file.write(NewData)
    file.close()

    CombineSignal(LatLonOutput, AntDataFile, FinalOutputFile)
    PlotData(FinalOutputFile)




def CombineSignal(LatLonFile, AntDataFile, FinalDataOutput):

    file1 = open(LatLonFile, 'r')
    file2 = open(AntDataFile, 'r')
    signal_data = file2.readline().split()
    sig_time = 3600 * int(signal_data[1][0:2]) + 60 * int(signal_data[1][3:5]) + int(signal_data[1][6:8])
    tot_time = 0
    NewData = ''

    for line in file1:
        splice = line.split()
        if splice[1][0:2].isnumeric():
            tot_time = 3600 * int(splice[1][0:2]) + 60 * int(splice[1][3:5]) + int(splice[1][6:8])

            # Making sure our signal time is up to our recorded time I guess
            if sig_time < tot_time:
                while (sig_time < tot_time) or (signal_data == ''):
                    signal_data = file2.readline().split()
                    if signal_data == []:
                        break
                    if signal_data:
                        sig_time = 3600 * int(signal_data[1][0:2]) + 60 * int(signal_data[1][3:5]) + int(
                            signal_data[1][6:8])

            if tot_time == sig_time:
                add_data = ''.join((' '.join(splice), ' ', signal_data[2], ' ', signal_data[3], ' ', '\n'))
                NewData = ''.join((NewData, add_data))

        else:
            NewData = ''.join((NewData, ' '.join(splice), '\n'))
    #print(NewData)
    file = open(FinalDataOutput, 'w')
    file.write(NewData)
    file.close()

def PlotData(FinalDataFile):

    def points_to_text(best_points):
        out_string = 'Best Installation Points \n'
        for each in best_points:
            out_string = ''.join((out_string, 'Alt: ', str(each[0]), ' Compass: ', str(each[1]), ' Signal: ', str(each[2]), '\n'))
        return out_string[0:-2]

    def plot(alt_rel, heading, signal, best_points):

        best_points = points_to_text(best_points)

        plt.figure(''.join(('Flight Plan ', str(flight_num))), figsize=(8,8.5))
        plt.suptitle(''.join(('Flight Plan ', str(flight_num), ', Lat/Lon: ', str(lat_lon))), fontsize=20)
        cm = plt.cm.get_cmap('jet')
        X = heading
        Y = alt_rel
        Z = signal
        sc = plt.scatter(X, Y, c=Z, cmap =cm, s = 50, alpha=1)
        bar = plt.colorbar(sc)
        bar.set_label('Signal Strength (dBm)')
        plt.xlabel('Compass Direction (0° = N, 90° = E)')
        plt.ylabel('Altitude (Feet)')
        # Place a legend to the right of this smaller subplot.
        extra = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
        plt.legend([extra], (best_points, "0-10", "10-100"), bbox_to_anchor =(0.75, -0.075), loc=2, prop={'size':9})
        plt.subplots_adjust(bottom=0.19)
        plt.axes().grid()
        plt.axes().xaxis.set_ticks(np.arange(0, 405, 45))
        plt.show()

    def find_points(points, signal):
        current = signal
        for index in range(0, 5):
            if int(points[index][2]) < int(current[2]):
                push = points[index]
                points[index] = current
                current = push
        return points

    file = open(FinalDataFile, 'r')
    lat_lon = ''
    heading = []
    alt_asml = []
    alt_rel = []
    signal = []
    flight_num = 0
    best_points = [ ['0', '0', '-100'],   # alt, comp, sig
                    ['0', '0', '-100'],
                    ['0', '0', '-100'],
                    ['0', '0', '-100'],
                    ['0', '0', '-100'] ]

    for line in file:
        # Remove trailing new lines
        line = line[:(len(line) - 2)]
        split = line.split(' ')

        # Separate the flights, plot what you've got here, then clear things out (if more than one flight)
        if split[0] == 'Flight':
            flight_num += 1
            if len(split) > 3:
                lat_lon = ''.join((split[4], ' ', split[5]))
            if (len(heading) > 0):
                plot(alt_rel, heading, signal)
                # Clear variables in case there's anything more to come
                heading = []
                alt_asml = []
                alt_rel = []
                signal = []

        else:
            if split[1] != 'HH:MM:SS':
                heading.append(format(float(split[3]),'.5f'))
                alt_asml.append(format(float(split[5]), '.3f'))
                alt_rel.append(format(float(split[7]),'.5f'))
                sig = split[-1][:-3]
                signal.append((float(sig)))
                best_points = find_points(best_points, [alt_rel[-1], heading[-1], signal[-1]])

    plot(alt_rel, heading, signal, best_points)


GatherData('C:/Users/Dylan/Documents/UAVRT/Final Design Test/Test_Flight.txt',
           'C:/Users/Dylan/Documents/UAVRT/Final Design Test/LocAltData1.txt',
           'C:/Users/Dylan/Documents/UAVRT/Final Design Test/LatLonData1.txt',
            'C:/Users/Dylan/Documents/UAVRT/Final Design Test/AntData1.txt',
           'C:/Users/Dylan/Documents/UAVRT/Final Design Test/FinalData1.txt')
