import random
import time

import matlab.engine
import numpy as np

class device:
    def __init__(self,name):
        self.state = [0, 0, 0, 0, 0]
        self.name=name

    def attacked(self, atk: int):

        if atk == 1:
            self.state[atk - 1] = 1
        elif atk == 2 and self.state[0] == 1:
            self.state[atk - 1] = 1
        elif (atk == 3) and self.state[1] == 1:
            self.state[atk - 1] = 1
        elif (atk == 4) and self.state[2] == 1:
            self.state[atk - 1] = 1
        elif (atk == 5) and self.state[3] == 1:
            self.state[atk - 1] = 1
        else:
            pass
        return self.state

    def get_state(self):
        return self.state

    def isCompromised(self):
        return all(self.state)

    def get_alert(self):
        alert_level = 0
        if self.state[4] == 1:
            alert_level = 5
        elif self.state[3] == 1:
            alert_level = 4
        elif self.state[2] == 1:
            alert_level = 3
        elif self.state[1] == 1:
            alert_level = 2
        elif self.state[0] == 1:
            alert_level = 1
        else:
            pass
        return alert_level

    def reImage(self):
        self.state = [0, 0, 0, 0, 0]

    def step(self):
        alert_level = 0
        if random.random() < 0.0005:
            alert_level = 5
        elif random.random() < 0.001:
            alert_level = 4
        elif random.random() < 0.001:
            alert_level = 3
        elif random.random() < 0.001:
            alert_level = 2
        elif random.random() < 0.01:
            alert_level = 1
        else:
            if sum(self.state) != 0:
                alert_rate = 0.1
                if self.state[-1] == 1:
                    alert_rate += 0.7
                elif self.state[3]==1:
                    alert_rate+=0.6
                elif self.state[2]==1:
                    alert_rate+=0.5
                elif self.state[1]==1:
                    alert_rate+=0.4
                else:
                    alert_rate += 0.2
                if random.random() <= alert_rate:
                    if self.state[4] == 1:
                        alert_level = 5
                    elif self.state[3] == 1:
                        alert_level = 4
                    elif self.state[2] == 1:
                        alert_level = 3
                    elif self.state[1] == 1:
                        alert_level = 2
                    elif self.state[0] == 1:
                        alert_level = 1
                    else:
                        pass
        return alert_level

    def defense(self, mode=0):
        if mode == 1:
            self.state[0] = 0
        elif mode == 2:
            self.state[1] = 0
        elif mode == 3:
            self.state[2] = 0
        elif mode == 4:
            self.state[3] = 0
        elif mode == 5:
            self.reImage()
        else:
            pass

class attacker:
    def __init__(self, Vlan: list):
        self.isCompromised = []
        self.Vlan = Vlan
        self.vlanIndex = 0
        self.target = None
        self.phy_atk_flag = 1
        self.count = 0
        self.isDirect = 0
        self.lock=0

    def findVlan(self):
        vc0 = 0
        vc1 = 0
        vc2 = 0
        for item in self.Vlan[0]:
            if item.isCompromised():
                vc0 += 1
        for item in self.Vlan[1]:
            if item.isCompromised():
                vc1 += 1
        for item in self.Vlan[2]:
            if item.isCompromised():
                vc2 += 1

        if self.vlanIndex == 0 and vc0 >= 2:
            self.vlanIndex = 1
            return True
        elif self.vlanIndex == 1 and vc1 >= 3:
            self.vlanIndex = 2
            return True
        elif self.vlanIndex == 2 and vc2 >= 1:
            self.vlanIndex = 3
            return True
        else:
            return False

    def findTarget(self):
        targets = []
        for item in self.Vlan[self.vlanIndex]:
            if not item.isCompromised():
                targets.append(item)
        if not targets:
            return False
        target = targets[random.randint(0, len(targets) - 1)]
        self.target = target
        return True

    def attack(self, eng, env_name, t, actuators, sensors, direct=False):
        alert_level = 0
        if self.findVlan():
            # alert_rate = 0.05
            # if random.random() < alert_rate:
            alert_level = 1
            return None, alert_level

        if direct:
            if 12 < t < 36 and self.phy_atk_flag == 1 and random.random() < 0.1:
                self.vlanIndex = 3
                self.isDirect = 1

        if self.vlanIndex < 3:
            if not self.target:
                if self.findTarget():
                    alert_rate = 0.05
                    if random.random() < alert_rate:
                        alert_level = 1
                    return self.target, alert_level
                else:
                    return None, alert_level

            targetState = self.target.get_state()

            for i in range(len(targetState)):
                if targetState[i] == 0:
                    self.target.attacked(i + 1)
                    if i == 0:
                        alert_rate = 0.3
                    elif i==1:
                        alert_rate = 0.5
                    elif i == 2:
                        alert_rate = 0.6
                    elif i == 3:
                        alert_rate = 0.6
                    else:
                        alert_rate = 0.7
                    if random.random() < alert_rate:
                        if i ==0:
                            alert_level = 1
                        elif i ==1:
                            alert_level = 2
                        elif i ==2:
                            alert_level = 3
                        elif i ==3:
                            alert_level = 4
                        else:
                            alert_level = 5
                    break
                else:
                    pass

            target = self.target
            if self.target.isCompromised():
                self.isCompromised.append(self.target)
                self.target = None
            return target, alert_level
        else:
            # physics attack
            if self.phy_atk_flag != 0:
                target = self.count % 2
                self.count += 1
                if target == 0:
                    duration = eng.get_param(env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'duration')
                    if int(duration) == 0 and (self.lock==0):
                        self.lock=1
                        cur_indication = actuators[2]
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'start',
                                      str(t), nargout=0)
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'duration',
                                      str(10), nargout=0)
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'value',
                                      str(100), nargout=0)
                elif target == 1:
                    duration = eng.get_param(env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'duration')
                    if int(duration) == 0 and (self.lock==0):
                        self.lock = 1
                        cur_indication = actuators[4]
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'start',
                                      str(t), nargout=0)
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'duration',
                                      str(10), nargout=0)
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'value',
                                      str(0), nargout=0)
                elif target == 2:
                    duration = eng.get_param(env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'duration')
                    if int(duration) == 0:
                        print("attack_action_xmv7 ", t)
                        cur_indication = actuators[5]
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'start',
                                      str(t), nargout=0)
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'duration',
                                      str(72), nargout=0)
                        eng.set_param(env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'value',
                                      str(cur_indication + 0.3), nargout=0)
            return None, None
    def degeneration(self):
        for item in self.isCompromised:
            if not item.isCompromised():
                self.isCompromised.remove(item)
        if self.vlanIndex == 3:
            countVlan1 = 0
            countVlan2 = 0
            countVlan3 = 0
            for item in self.isCompromised:
                if item in self.Vlan[self.vlanIndex - 1]:
                    countVlan3 += 1
                if item in self.Vlan[self.vlanIndex - 2]:
                    countVlan2 += 1
                if item in self.Vlan[self.vlanIndex - 3]:
                    countVlan1 += 1
            if countVlan3 == 0:
                if countVlan2 == 0:
                    if countVlan1 == 0:
                        self.vlanIndex = 0
                        self.target = None
                    else:
                        self.vlanIndex = 1
                        self.target = None
                else:
                    self.vlanIndex = 2
                    self.target = None
        if self.vlanIndex == 2:
            countVlan1 = 0
            countVlan2 = 0
            countVlan3 = 0
            for item in self.isCompromised:
                if item in self.Vlan[self.vlanIndex]:
                    countVlan3 += 1
                if item in self.Vlan[self.vlanIndex - 1]:
                    countVlan2 += 1
                if item in self.Vlan[self.vlanIndex - 2]:
                    countVlan1 += 1
            if countVlan3 == 0:
                if countVlan2 == 0:
                    if countVlan1 == 0:
                        self.vlanIndex = 0
                        self.target = None
                    else:
                        self.vlanIndex = 1
                        self.target = None
        if self.vlanIndex == 1:
            countVlan1 = 0
            countVlan2 = 0
            for item in self.isCompromised:
                if item in self.Vlan[self.vlanIndex]:
                    countVlan2 += 1
                if item in self.Vlan[self.vlanIndex - 1]:
                    countVlan1 += 1
            if countVlan2 == 0:
                if countVlan1 == 0:
                    self.vlanIndex = 0
                    self.target = None

    def get_atk_stage(self):
        return self.vlanIndex

    def reset(self):
        self.isCompromised = []
        self.vlanIndex = 0
        self.target = None
        self.phy_atk_flag = 1
        self.isDirect = 0
        self.lock = 0

    def getDirect(self):
        return self.isDirect

class cross_layer_Sim:
    def __init__(self, stop_step=48, env_name='TEModel'):
        self.step_count = 0
        self.ep = -2
        self.WS = device('WS_IN1')
        self.DB = device('DB_IN1')
        self.DNS = device('DNS_IN1')

        self.PM1 = device('PC1_IN2')
        self.PM2 = device('PC2_IN2')
        self.PM3 = device('PC3_IN2')
        self.WS1 = device('WS_IN2')

        self.ES = device('ES_IN3')
        self.CS = device('CS_IN3')

        self.Vlan1 = [self.WS, self.DB,self.DNS]
        self.Vlan2 = [self.PM1, self.PM2, self.PM3,self.WS1]
        self.Vlan3 = [self.ES, self.CS]

        self.Physics = []
        self.allDevice = [self.WS, self.DB, self.DNS,self.PM1, self.PM2, self.PM3, self.WS1,self.ES, self.CS]
        self.device_state = [self.WS.get_state(), self.DB.get_state(), self.DNS.get_state(),self.PM1.get_state(), self.PM2.get_state(),
                             self.PM3.get_state(), self.WS1.get_state(),self.ES.get_state(), self.CS.get_state()]
        self.alerts = [0, 0, 0,0,0, 0, 0, 0, 0]
        self.cost = 0

        self.physic_state = np.array(
            [np.float32(2800.0), np.float32(50.0), np.float32(53.724), np.float32(26.4403), np.float32(26.7475),
             np.float32(36.7264)], dtype=np.float32)

        self.env_name = env_name

        self.eng = matlab.engine.start_matlab()
        root_dir = r'E:\soft\code\pyth_code\ziqi'
        sim_dir = r'E:\soft\code\pyth_code\ziqi\sim'
        model_dir = r'E:\soft\code\pyth_code\ziqi\model'
        self.eng.addpath(self.eng.genpath(root_dir), nargout=0)
        self.eng.addpath(sim_dir, nargout=0)
        self.eng.addpath(model_dir, nargout=0)
        self.eng.cd(model_dir, nargout=0)
        self.eng.load_system(self.env_name, nargout=0)
        self.eng.eval("initModel", nargout=0)
        print("Ts_base exists:", self.eng.eval("exist('Ts_base','var')"))
        print("xmv3_0 exists:", self.eng.eval("exist('xmv3_0','var')"))
        print("xmv exists:", self.eng.eval("exist('xmv','var')"))

        self.eng.set_param(self.env_name, 'StopTime', str(stop_step), nargout=0)
        self.step_count = 0
        self.stop_step = stop_step
        self.real_sensors = []
        self.real_actuators = []
        self.fake_actuators = []
        self.fake_sensors = []
        self.cur_time = 0
        self.defense_time = stop_step
        self.node_score = 0
        self.previous_physic_state=[]

        self.attacker = attacker([self.Vlan1, self.Vlan2, self.Vlan3, self.Physics])

    def step(self, action):
        time_cost = 0
        defense_succ = False
        succ = 0
        cost = 0
        property_loss = 0
        self.step_count += 1
        self.cur_time = round(float(self.eng.get_param(self.env_name + '/Pause', 'Value')), 3)
        self.eng.set_param(self.env_name + '/Pause', 'Value', str(self.cur_time + 0.2), nargout=0)

        direct = False
        xmvs = np.array(self.eng.eval('xmv'))
        self.real_actuators = [xmvs[-1][0], xmvs[-1][1], xmvs[-1][2], xmvs[-1][3], xmvs[-1][5], xmvs[-1][6],
                               xmvs[-1][7], xmvs[-1][9], xmvs[-1][10]]

        target, alert_level = self.attacker.attack(self.eng, self.env_name, self.cur_time, self.real_actuators,
                                                   self.real_sensors, direct)

        compromised_device=[]
        for item in self.attacker.isCompromised:
            compromised_device.append(item.name)

        self.step_count += 1
        atk_stage = self.attacker.get_atk_stage()
        isDirect = self.attacker.getDirect()
        if target==None:
            target_name=None
        else:
            target_name=target.name
        if action == 0:
            self.WS.defense(1)
            cost += 2
        elif action == 1:
            self.WS.defense(2)
            cost += 4
        elif action == 2:
            self.WS.defense(3)
            cost += 6
        elif action == 3:
            self.WS.defense(4)
            cost += 8
        elif action == 4:
            self.DB.defense(1)
            cost += 2
        elif action == 5:
            self.DB.defense(2)
            cost += 4
        elif action == 6:
            self.DB.defense(3)
            cost += 6
        elif action == 7:
            self.DB.defense(4)
            cost += 8
        elif action == 8:
            self.PM1.defense(1)
            cost += 2
        elif action == 9:
            self.PM1.defense(2)
            cost += 4
        elif action == 10:
            self.PM1.defense(3)
            cost += 6
        elif action == 11:
            self.PM1.defense(4)
            cost += 8
        elif action == 12:
            self.PM2.defense(1)
            cost += 2
        elif action == 13:
            self.PM2.defense(2)
            cost += 4
        elif action == 14:
            self.PM2.defense(3)
            cost += 6
        elif action == 15:
            self.PM2.defense(4)
            cost += 8
        elif action == 16:
            self.PM3.defense(1)
            cost += 2
        elif action == 17:
            self.PM3.defense(2)
            cost += 4
        elif action == 18:
            self.PM3.defense(3)
            cost += 6
        elif action == 19:
            self.PM3.defense(4)
            cost += 8
        elif action == 20:
            self.ES.defense(1)
            cost += 2
        elif action == 21:
            self.ES.defense(2)
            cost += 4
        elif action == 22:
            self.ES.defense(3)
            cost += 6
        elif action == 23:
            self.ES.defense(4)
            cost += 8
        elif action == 24:
            self.CS.defense(1)
            cost += 2
        elif action == 25:
            self.CS.defense(2)
            cost += 4
        elif action == 26:
            self.CS.defense(3)
            cost += 6
        elif action == 27:
            self.CS.defense(4)
            cost += 8
        elif action == 28:
            self.ES.defense(5)
            cost += 10
        elif action == 29:
            self.WS.defense(5)
            cost += 10
        elif action == 30:
            self.DB.defense(5)
            cost += 10
        elif action == 31:
            self.PM1.defense(5)
            cost += 10
        elif action == 32:
            self.PM2.defense(5)
            cost += 10
        elif action == 33:
            self.PM3.defense(5)
            cost += 10
        elif action == 34:
            self.CS.defense(5)
            cost += 10
        elif action == 35:
            self.DNS.defense(1)
            cost += 2
        elif action == 36:
            self.DNS.defense(2)
            cost += 4
        elif action == 37:
            self.DNS.defense(3)
            cost += 6
        elif action == 38:
            self.DNS.defense(4)
            cost += 8
        elif action == 39:
            self.DNS.defense(5)
            cost += 10
        elif action == 40:
            self.WS1.defense(1)
            cost += 2
        elif action == 41:
            self.WS1.defense(2)
            cost += 4
        elif action == 42:
            self.WS1.defense(3)
            cost += 6
        elif action == 43:
            self.WS1.defense(4)
            cost += 8
        elif action == 44:
            self.WS1.defense(5)
            cost += 10
        elif (action == 45) or (action==46):
             return self.step_phy_ac(action,target, alert_level)

        else:
            pass

        self.eng.set_param(self.env_name, 'SimulationCommand', 'continue', nargout=0)
        simout = np.array(self.eng.eval('simout'))
        self.real_sensors = [simout[-1][0], simout[-1][1], simout[-1][2], simout[-1][3], simout[-1][6],
                             simout[-1][7], simout[-1][8], simout[-1][9], simout[-1][10], simout[-1][11],
                             simout[-1][13], simout[-1][14], simout[-1][16], simout[-1][34],simout[-1][39]]
        xmvs = np.array(self.eng.eval('xmv'))
        self.real_actuators = [xmvs[-1][0], xmvs[-1][1], xmvs[-1][2], xmvs[-1][3], xmvs[-1][5], xmvs[-1][6],
                               xmvs[-1][7], xmvs[-1][9], xmvs[-1][10]]

        self.physic_state[0] = np.array([simout[-1][6]], dtype=np.float32)  # pressure
        self.physic_state[1] = np.array([simout[-1][10]], dtype=np.float32)  # separator temp
        self.physic_state[2] = np.array([simout[-1][11]], dtype=np.float32)  # separator level
        self.physic_state[3] = np.array([simout[-1][34]], dtype=np.float32)  # compont g in purge

        if self.physic_state[0] > 2980:
            property_loss = 100

        if self.physic_state[0] > 2980:
            property_loss = 100
        if (self.real_sensors[5] * 6.667 + 84.6) / 35.3145 > 23 or (
                self.real_sensors[5] * 6.667 + 84.6) / 35.3145 < 3:
            property_loss = 100
        if (self.real_sensors[9] * 2.9 + 27.5) / 35.3145 > 11 or (
                self.real_sensors[9] * 2.9 + 27.5) / 35.3145 < 2:
            property_loss = 100
        if (self.real_sensors[11] * 1.565 + 78.25) / 35.3415 > 7 or (
                self.real_sensors[11] * 1.565 + 78.25) / 35.3415 < 2:
            property_loss = 100

        if self.cur_time >= self.stop_step:
            duration1 = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/',
                                           'duration')
            duration2 = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/',
                                           'duration')
            duration3 = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv7 attack controller/',
                                           'duration')
            if int(duration1) or int(duration2) or int(duration3) != 0:
                property_loss = 100
        deviation = round(abs((self.physic_state[0] - 2799) / 1.2645) \
                          + abs((self.physic_state[2] - 49.9724) / 10),5)
        self.attacker.degeneration()
        atk_stage = self.attacker.get_atk_stage()
        alerts = [0, 0, 0, 0, 0, 0, 0,0,0]
        for i in range(len(self.allDevice)):
            alert_level = self.allDevice[i].step()
            alerts[i] = alert_level
        if (target not in self.attacker.isCompromised):
            pass
        else:
            if alerts[self.allDevice.index(target)] < alert_level:
                alerts[self.allDevice.index(target)] = alert_level
        self.alerts = alerts
        node_score = 0
        for i in range(len(self.allDevice)):
            if self.allDevice[i].isCompromised():
                if i < 2:
                    vlan_score = 1
                elif i < 5:
                    vlan_score = 2
                else:
                    vlan_score = 3
                node_score += vlan_score + self.allDevice[i].get_alert()
        reward = succ - 0.03 * deviation - 0.02 * cost - 0.05 * node_score
        self.node_score += node_score
        self.cost += round(cost, 1)
        node_compromised = 0
        for i in range(len(self.allDevice)):
            if self.allDevice[i].isCompromised():
                node_compromised += 1
        return reward, round(cost, 1), property_loss, deviation, atk_stage, node_compromised, isDirect

    def step_phy_ac(self, action,target, alert_level):
        previous_physic_state=[]
        current_physic_state=[]
        time_cost = 0
        defense_succ = False
        succ = 0
        cost = 0
        # loss = 0
        property_loss = 0
        self.step_count += 1
        atk_stage = self.attacker.get_atk_stage()
        isDirect = self.attacker.getDirect()
        if  action == 45:
            duration = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'duration')
            if int(duration) != 0:
                defense_succ = True
                start_time = round(float(
                    self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'start')), 3)
                time_cost = self.cur_time - start_time
                self.defense_time = self.cur_time
            self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'duration',
                               str(0), nargout=0)
            cost += 12
        elif action == 46:
            duration = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'duration')
            if int(duration) != 0:
                defense_succ = True
                start_time = round(float(
                    self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'start')), 3)
                time_cost = self.cur_time - start_time
                self.defense_time = self.cur_time
            self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'duration',
                               str(0), nargout=0)
            cost += 12
        else:
            pass

        simout = np.array(self.eng.eval('simout'))
        self.real_sensors = [simout[-1][0], simout[-1][1], simout[-1][2], simout[-1][3], simout[-1][6],
                             simout[-1][7], simout[-1][8], simout[-1][9], simout[-1][10], simout[-1][11],
                             simout[-1][13], simout[-1][14], simout[-1][16], simout[-1][34],simout[-1][39]]

        previous_physic_state.append(np.array([simout[-1][6]], dtype=np.float32))
        previous_physic_state.append(np.array([simout[-1][10]], dtype=np.float32))
        previous_physic_state.append(np.array([simout[-1][11]], dtype=np.float32))
        previous_physic_state.append(np.array([simout[-1][34]], dtype=np.float32))
        previous_devaition=abs(previous_physic_state[0]-2799)/2799+abs(previous_physic_state[1]-91.81)/91.81\
                           +abs(previous_physic_state[2]-50)/50+abs(previous_physic_state[3]-6.6386)/6.6386
        previous_devaition1 = abs(previous_physic_state[0] - 2799) / 2799
        self.eng.set_param(self.env_name, 'SimulationCommand', 'continue', nargout=0)
        simout = np.array(self.eng.eval('simout'))
        current_physic_state.append(np.array([simout[-1][6]], dtype=np.float32))
        current_physic_state.append(np.array([simout[-1][10]], dtype=np.float32))
        current_physic_state.append(np.array([simout[-1][11]], dtype=np.float32))
        current_physic_state.append(np.array([simout[-1][34]], dtype=np.float32))
        current_devaition = abs(current_physic_state[0] - 2800) / 2800 + abs(current_physic_state[1] - 91.81) / 91.81 \
                             + abs(current_physic_state[2] - 50) / 50 + abs(current_physic_state[3] - 6.6386) / 6.6386
        current_devaition1 = abs(current_physic_state[0] - 2799) / 2799
        if (previous_physic_state[0]>current_physic_state[0]) and (abs(previous_physic_state[0]-current_physic_state[0])>=10):
            deviation=self.step_phy_ac_to_normal(action,current_devaition1)
        else:
            deviation = np.round(abs((current_physic_state[0] - 2799) / 1.2645) \
                              + abs((current_physic_state[2] - 49.9724) / 10) , 5)
        deviation = float(deviation)
        simout = np.array(self.eng.eval('simout'))
        self.physic_state[0] = np.array([simout[-1][6]], dtype=np.float32)  # pressure
        self.physic_state[1] = np.array([simout[-1][10]], dtype=np.float32)  # separator_level
        self.physic_state[2] = np.array([simout[-1][11]], dtype=np.float32)  # separator temp
        self.physic_state[3] = np.array([simout[-1][34]], dtype=np.float32)  # compont g in purge

        if self.physic_state[0] > 2980:
            property_loss = 100
        if self.cur_time >= self.stop_step:
            duration1 = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/',
                                           'duration')
            duration2 = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/',
                                           'duration')
            duration3 = self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv7 attack controller/',
                                           'duration')
            if int(duration1) or int(duration2) or int(duration3) != 0:
                property_loss = 100


        if property_loss != 0:
            xmv3_start = round(
                float(self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/',
                                         'start')), 3)
            xmv6_start = round(
                float(self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/',
                                         'start')), 3)
            xmv7_start = round(
                float(self.eng.get_param(self.env_name + '/TE Plant/xmv atk block/xmv7 attack controller/',
                                         'start')), 3)
            time_cost = max(self.cur_time - xmv3_start, self.cur_time - xmv6_start, self.cur_time - xmv7_start)

        self.attacker.degeneration()
        atk_stage = self.attacker.get_atk_stage()
        alerts = [0, 0, 0, 0, 0, 0, 0,0,0]
        for i in range(len(self.allDevice)):
            alert_level = self.allDevice[i].step()
            alerts[i] = alert_level

        if (target not in self.attacker.isCompromised):
            pass
        else:
            if alerts[self.allDevice.index(target)] < alert_level:
                alerts[self.allDevice.index(target)] = alert_level
        self.alerts = alerts

        node_score = 0

        for i in range(len(self.allDevice)):
            if self.allDevice[i].isCompromised():
                if i < 2:
                    vlan_score = 1
                elif i < 5:
                    vlan_score = 2
                else:
                    vlan_score = 3
                node_score += vlan_score + self.allDevice[i].get_alert()
        reward = succ - 0.02 * deviation - 0.02 * cost - 0.06 * node_score

        self.node_score += node_score
        self.cost += round(cost, 1)
        node_compromised = 0
        for i in range(len(self.allDevice)):
            if self.allDevice[i].isCompromised():
                node_compromised += 1
        return reward, round(cost, 1), property_loss, deviation, atk_stage, node_compromised, isDirect

    def step_phy_ac_to_normal(self, action,current_devaition):

        current_physic_state = [0, 0, 0, 0]
        current_devaition1 = current_devaition
        simout = np.array(self.eng.eval('simout'))
        current_physic_state[0] = np.array([simout[-1][6]], dtype=np.float32)  # pressure 2800
        current_physic_state[1] = np.array([simout[-1][10]], dtype=np.float32)  # separator temp 91.81
        current_physic_state[2] = np.array([simout[-1][11]], dtype=np.float32)  # separator_level 50
        current_physic_state[3] = np.array([simout[-1][34]], dtype=np.float32)  # compont g in purge 6.6386
        self.step_count += 1
        while(current_devaition1>0.001 or abs(current_physic_state[1]-91.8)>0.5 or abs(current_physic_state[2]-50)>3.1):
            self.cur_time = round(float(self.eng.get_param(self.env_name + '/Pause', 'Value')), 3)

            self.eng.set_param(self.env_name + '/Pause', 'Value', str(self.cur_time + 0.2), nargout=0)

            self.eng.set_param(self.env_name, 'SimulationCommand', 'continue', nargout=0)

            simout = np.array(self.eng.eval('simout'))

            if(simout.shape[0]==4801):
                break
            current_physic_state[0] = np.array([simout[-1][6]], dtype=np.float32) # pressure 2800
            current_physic_state[1]=np.array([simout[-1][10]], dtype=np.float32) # separator temp 91.81
            current_physic_state[2]=np.array([simout[-1][11]], dtype=np.float32)  # separator_level 50
            current_physic_state[3]=np.array([simout[-1][34]], dtype=np.float32)  # compont g in purge 6.6386

            current_devaition = abs(current_physic_state[0] - 2800) / 2800 + abs(current_physic_state[1] - 91.81) / 91.81 \
                                + abs(current_physic_state[2] - 50) / 50 + abs( current_physic_state[3] - 6.6386) / 6.6386

            current_devaition1 = abs(current_physic_state[0] - 2799) / 2799

        deviation = np.round(abs((current_physic_state[0] - 2799.0) / 1.2645) \
                          + abs((current_physic_state[2] - 49.9724) / 10),5)
        self.attacker.lock=0
        return deviation
    def get_obs(self):
        alert_in_phy = [0, 0, 0, 0]
        if (abs(self.physic_state[0] - 2799) <= 5):
            alert_in_phy[0] = 3
        elif abs(self.physic_state[0] - 2799) <= 50:
            alert_in_phy[0] = 4
        elif abs(self.physic_state[0] - 2799) <= 100:
            alert_in_phy[0] = 5
        else:
            alert_in_phy[0] = 6

        if (abs(self.physic_state[1] - 91.8) <= 0.6):
            alert_in_phy[1] = 3
        elif abs(self.physic_state[1] - 91.8) <= 1.5:
            if self.physic_state[1] >= 91.8:
                alert_in_phy[1] = 4
            else:
                alert_in_phy[1] = 2
        elif abs(self.physic_state[1] - 91.8) <= 3:
            if self.physic_state[1] >= 91.8:
                alert_in_phy[1] = 5
            else:
                alert_in_phy[1] = 1
        else:
            if self.physic_state[1] >= 91.8:
                alert_in_phy[1] = 6
            else:
                alert_in_phy[1] = 0

        if (abs(self.physic_state[2] - 50) <= 3.1):
            alert_in_phy[2] = 3
        elif abs(self.physic_state[2] - 50) <= 5:
            if self.physic_state[2] >= 50:
                alert_in_phy[2] = 4
            else:
                alert_in_phy[2] = 2
        elif abs(self.physic_state[2] - 50) <= 10:
            if self.physic_state[2] >= 50:
                alert_in_phy[2] = 5
            else:
                alert_in_phy[2] = 1
        else:
            if self.physic_state[2] >= 50:
                alert_in_phy[2] = 6
            else:
                alert_in_phy[2] = 0

        if (abs(self.physic_state[3] - 6.6386) <= 0.5):
            alert_in_phy[3] = 3
        elif abs(self.physic_state[3] - 6.6386) <= 1:
            if self.physic_state[3] >= 6.6386:
                alert_in_phy[3] = 4
            else:
                alert_in_phy[3] = 2
        elif abs(self.physic_state[3] - 6.6386) <= 2:
            if self.physic_state[3] >= 6.6386:
                alert_in_phy[3] = 5
            else:
                alert_in_phy[3] = 1
        else:
            if self.physic_state[3] >= 6.6386:
                alert_in_phy[3] = 6
            else:
                alert_in_phy[3] = 0

        state = self.alerts + alert_in_phy
        return state


    def get_alerts(self):
        return np.array(self.alerts)

    def sim(self):
        pass
    def isDone(self):
        if self.cur_time >= self.stop_step:
            return 2
        elif self.physic_state[0] > 2980:
            return 1
        else:
            return 0

    def reset(self):
        self.ep += 1
        for dev in self.allDevice:
            dev.reImage()
        self.alerts = [0, 0, 0, 0, 0, 0, 0,0,0]
        self.physic_state = np.array(
            [np.float32(2799.0), np.float32(91.8), np.float32(50), np.float32(6.6386), np.float32(26.7475),
             np.float32(36.7264)], dtype=np.float32)
        self.attacker.reset()
        self.step_count = 0
        self.defense_time = self.stop_step

        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'atkMode',
                           'Interval attack', nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'atkMode',
                           'Interval attack', nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'atkMode',
                           'Interval attack', nargout=0)

        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'switch_mode',
                           'Integrity attack', nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'switch_mode',
                           'Integrity attack', nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'switch_mode',
                           'Integrity attack', nargout=0)

        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'start',
                           str(self.stop_step), nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv3 attack controller/', 'duration',
                           str(0), nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'start',
                           str(self.stop_step), nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv6 attack controller/', 'duration',
                           str(0), nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'start',
                           str(self.stop_step), nargout=0)
        self.eng.set_param(self.env_name + '/TE Plant/xmv atk block/xmv7 attack controller/', 'duration',
                           str(0), nargout=0)
        self.cur_time = round(float(0.1), 3)
        self.eng.set_param(self.env_name, 'SimulationCommand', 'stop', nargout=0)
        self.eng.set_param(self.env_name + '/Pause', 'Value', str(round(0.1, 3)), nargout=0)
        self.eng.set_param(self.env_name, 'SimulationCommand', 'start', nargout=0)

    def show(self):
        device_state = []
        for dev in self.allDevice:
            device_state.append(dev.get_state())

        print("------------------------------------")
        print("alerts:", self.alerts)
        print("states:", device_state)
        print("physics:", self.physic_state)
        print("------------------------------------")
        pass