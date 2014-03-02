import sys
from com.l2jserver.gameserver.model.quest		import State
from com.l2jserver.gameserver.model.quest		import QuestState
from com.l2jserver.gameserver.model.quest.jython	import QuestJython as JQuest

from com.l2jserver.gameserver.datatables import NpcTable
from com.l2jserver.gameserver.datatables import SpawnTable

import _codecs
from com.l2jserver.gameserver.instancemanager import RaidBossSpawnManager
from com.l2jserver.gameserver.instancemanager.RaidBossSpawnManager import StatusEnum
from com.l2jserver.gameserver import GameTimeController
from com.l2jserver.gameserver.model import L2World
from com.l2jserver.gameserver.instancemanager import DayNightSpawnManager

#execfile("data/scripts/custom/rbtools/npcname_gen_sql.py")

class NpcNameTable:
	npcNameTable = {}
	def __init__(self):
		f = open("data/scripts/custom/rbtools/npcname-tw.txt", "r")
		f.readline()
		for line in f:
			temp = line.split("\t")
			if temp[0].isdigit():
				self.npcNameTable[int(temp[0])] = _codecs.utf_8_decode(temp[1])[0]
		f.close()

	def getTable(self):
		return self.npcNameTable
			
	def getName(self, id):
		assert type(id) == type(0)
		try:
			return self.npcNameTable[id]
		except:
			return ""

		
class RBTools(JQuest):
	qID = -1
	qn = "RBTools"
	qDesc = "custom"
	
	isNoDataShow = True #�S�����͸�� �O�_���
	isAllowTeleInCombat = False #����԰����i�_�ǰe
	isAllowTeleDead = True #���⦺�`�i�_�ǰe
	backlist = [] #�¦W�� ���y���� ID [123,456]
	backlistByName = ["�Ȯ��_�`��","�g�cĵ�ö���","�g�c�u��"] #�¦W�� ���y������W
	
	NPCID = [102] #Ĳ�o���Ȫ� NPC �i�ק�.. �i�H�h ID �Ҧp [100,102,103]
	
	require_item = 57 #�һݹD��
	require_item_count = 1 #�һݹD��ƶq
	
	htm_header = "<html><body><title>���y����u��</title>"
	htm_footer = "</body></html>"
	htm_no_rights = "<center>��p �A�S���v��</center>"

	htm_intro_respawn_all = "<a action=\"bypass -h Quest " + qn + " respawnAll\">��������(GM��)</a><BR>"
	htm_intro_list = "<a action=\"bypass -h Quest " + qn + " self\">�d�ݦC��(�ӤH�ǰe�Ҧ�)</a><BR>"
	htm_intro_party_list = "<a action=\"bypass -h Quest " + qn + " party\">�d�ݦC��(����ǰe�Ҧ�)</a><BR>"

	htm_menu = htm_intro_respawn_all + htm_intro_list + htm_intro_party_list
	htm_intro = "²��<BR>�Цۦ�ק�²��......<BR><font color=ff0000>�`�N �ǰe�N�|���� ����1��</font><BR>" + htm_menu

	pages = {"2x":[], "3x":[], "4x":[], "5x":[], "6x":[], "7x":[], "8x":[]}
	
	def getNpcIDsByName(self, name):
		if not self.npcNameTable: return []
		return [id for id, npc_name in self.npcNameTable.getTable().items() if npc_name == name]
	
	def __init__(self, id = qID, name = qn, descr = qDesc):
		JQuest.__init__(self, id, name, descr)
		for id in self.NPCID:
			self.addStartNpc(id)
			self.addFirstTalkId(id)
			self.addTalkId(id)
		self.npcNameTable = NpcNameTable()
		#init pages
		rb_id = {}
		bosses = NpcTable.getInstance().getAllNpcOfClassType(["L2RaidBoss"])
		for boss in bosses:
			lv = boss.getLevel()
			if lv not in rb_id:
				rb_id[lv] = []
			rb_id[lv] += [boss.getNpcId()]
		rb_id = rb_id.items()
		rb_id.sort()
		for lv,id_list in rb_id:
			if lv in xrange(20,30):
				self.pages["2x"] += [[lv, id_list]]
			elif lv in xrange(30,40):
				self.pages["3x"] += [[lv, id_list]]
			elif lv in xrange(40,50):
				self.pages["4x"] += [[lv, id_list]]
			elif lv in xrange(50,60):
				self.pages["5x"] += [[lv, id_list]]
			elif lv in xrange(60,70):
				self.pages["6x"] += [[lv, id_list]]
			elif lv in xrange(70,80):
				self.pages["7x"] += [[lv, id_list]]
			elif lv in xrange(80,90):
				self.pages["8x"] += [[lv, id_list]]
		for name in self.backlistByName:
			self.backlist += self.getNpcIDsByName(name)
		print "Init:" + self.qn + " loaded", "rb:", len(bosses), "backlist:", len(self.backlist)
	
	def getPageHtm(self, player, selected_tab="2x"):
		def getTabHtm():
			keys = self.pages.keys()
			keys.sort()
			r = "<table border=0 cellpadding=0 cellspacing=0><tr>"
			for key in keys:
				r += "<td><button width=30 height=20 fore=\"L2UI_CT1.Tab_DF_Tab"
				if selected_tab == key:
					r += "_Selected"
				else:
					r += "_Unselected"
				r += "\" value=\"" + key + "\" action=\"bypass -h Quest " + self.qn + " " + key + "\"></td>"
			r += "</tr></table>"
			return r
		rbsm = RaidBossSpawnManager.getInstance()
		l2world = L2World.getInstance()
		r = "<table border=0 cellpadding=0 cellspacing=0>"
		for id, id_list in self.pages.items():
			if id == selected_tab:
				for lv, ids in id_list:
					for npc_id in ids:
						if npc_id in self.backlist:
							continue
						status = rbsm.getRaidBossStatusId(npc_id)
						if status == StatusEnum.UNDEFINED:
							if not self.isNoDataShow:
								continue
						npc = self.getL2Npc(npc_id)
						v = None
						if npc:
							v = l2world.findObject(npc.getObjectId())
							isInCombat = npc.isInCombat()
						r += "<tr>"
						r += "<td width=30>"
						showTele = False
						if not status == StatusEnum.UNDEFINED:# and v:
							if not status == StatusEnum.DEAD or self.isAllowTeleDead:
								showTele = True
							if v:
								if not isInCombat or self.isAllowTeleInCombat:
									showTele = True
						if showTele:
							r += "<a action=\"bypass -h Quest " + self.qn + " teleport_" + str(npc_id) + "\">" + "�ǰe" + "</a>"
						r += "</td>"
						r += "<td>Lv" + str(lv) + " " + self.npcNameTable.getName(npc_id) + "(" + str(npc_id) + ")</td>"
						if status == StatusEnum.ALIVE:
							if v:
								if isInCombat:
									r += "<td><font color=FF0000>�D�Ԥ�</font></td>"
								else:
									r += "<td>�i�D��</td>"
							else:
								r += "<td>����</td>"
						elif status == StatusEnum.DEAD:
							if v:
								r += "<td>���`</td>"
							else:
								if player.isGM():
									r += "<td><a action=\"bypass -h Quest " + self.qn + " respawn_" + str(npc_id) + "\">" + "GM����" + "</a></td>"
								else:
									r += "<td>�ݭ���</td>"
						else:
							r+= "<td><font color=666666>�S�ƾ�</font></td>"
						r += "</tr>"
				break
		r += "</table>"
		return self.htm_header + getTabHtm() + r + self.htm_footer

	def getRbSpawn(self, bossid):
		bossid = int(bossid)
		rbsm = RaidBossSpawnManager.getInstance()
		spawns = rbsm.getSpawns()
		for id in spawns:
			if id == bossid:
				return spawns[id]
		return None

	def getL2Npc(self, bossid):
		spawn = self.getRbSpawn(bossid)
		if spawn:
			return spawn.getLastSpawn()
		return None

	def getRBInstance(self, bossid):
		bossid = int(bossid)
		rbsm = RaidBossSpawnManager.getInstance()
		bosses = rbsm.getBosses()
		for id in bosses:
			if id == bossid:
				return bosses[id]
		return None
		
	def respawn_all(self):
		rbsm = RaidBossSpawnManager.getInstance()
		for id, id_list in self.pages.items():
			for lv, ids in id_list:
				map(self.respawn, [npc_id for npc_id in ids if rbsm.getRaidBossStatusId(npc_id) == StatusEnum.DEAD])
	
	def respawn(self, bossid):
		spawn = self.getRbSpawn(bossid)
		if spawn:
			npc_t = spawn.getTemplate()
			if not npc_t: return
			hp, mp = npc_t.getBaseHpMax(), npc_t.getBaseMpMax()
			boss = self.getRBInstance(bossid)
			if boss and L2World.getInstance().findObject(boss.getObjectId()): return
			spawn.stopRespawn()
			rbsm = RaidBossSpawnManager.getInstance()
			rbsm.deleteSpawn(spawn, True)
			rbsm.addNewSpawn(spawn, 0, hp, mp, True)
			if npc_t.getNpcId() in [25328]: #25328 "�㺸�����w �� ����"
				if GameTimeController.getInstance().isNowNight(): 
					spawn.startRespawn()
					spawn.respawnNpc(spawn.getLastSpawn())
					spawn.stopRespawn()
					# spawn.doSpawn()
			return

	def teleport(self, player, bossid):
		st = player.getQuestState(self.qn)
		if not st:
			return
		mode = st.get("mode")
		if not mode:
			return
		pl = [player]
		if mode == "party":
			party = player.getParty()
			if not party:
				player.sendMessage("����Ҧ��ǰe ���A�S���ն�")
				return
			if not party.isLeader(player):
				player.sendMessage("����Ҧ��ǰe �u�������ϥ�")
				return
			#for m in party.getMembers(): #GS 883 �Τ���
			for m in party.getPartyMembers(): #GS 883 ���e
				pl += [m]
				if not player.isInsideRadius(m, 1000, False, False):
					player.sendMessage("����Ҧ��ǰe ���� %s ���b�d��" % m.getName())
					return
		if not player.destroyItemByItemId(self.qn, self.require_item, self.require_item_count, None, True):
			return
		x = y = z = None
		npc = self.getL2Npc(bossid)
		if npc:
			x,y,z = npc.getX(), npc.getY(), npc.getZ()
		else:
			spawn = self.getRbSpawn(bossid)
			if spawn:
				x,y,z = spawn.getLocx(), spawn.getLocy(), spawn.getLocz()
		for p in pl:
			p.teleToLocation(x + self.getRandom(50), y + self.getRandom(50), z + 20, 0, True)

		
	def onAdvEvent(self, event, npc, player):
		if event in self.pages:
			return self.getPageHtm(player, event)
		elif event == "respawnAll":
			if player.isGM():
				self.respawn_all()
			else:
				return self.htm_header + self.htm_no_rights + self.htm_footer
		elif event.startswith("respawn_"):
			if player.isGM():
				event = event.split("_")[1]
				self.respawn(event)
			else:
				return self.htm_header + self.htm_no_rights + self.htm_footer
		elif event.startswith("teleport_"):
			event = event.split("_")[1]
			self.teleport(player, event)
			return ''
		elif event in ["self","party"]:
			st = player.getQuestState(self.qn)
			if not st:
				return
			st.set("mode", event)
			return self.getPageHtm(player)
		return self.onFirstTalk(npc, player)
		
	def onFirstTalk(self, npc, player):
		st = player.getQuestState(self.qn)
		if not st:
			st = self.newQuestState(player)
			st.setState(State.STARTED)
		return self.htm_header + self.htm_intro + self.htm_footer
		
RBTools()
