import sys
from com.l2jserver.gameserver.model.quest		import State
from com.l2jserver.gameserver.model.quest		import QuestState
from com.l2jserver.gameserver.model.quest.jython	import QuestJython as JQuest

from com.l2jserver.gameserver.model.items.instance.L2ItemInstance import ItemLocation
from com.l2jserver.gameserver.datatables import ItemTable
from com.l2jserver.gameserver.network.serverpackets import SystemMessage
from com.l2jserver.gameserver.network import SystemMessageId
from com.l2jserver.gameserver.network.serverpackets import EnchantResult
from com.l2jserver.gameserver.network.serverpackets import StatusUpdate
from com.l2jserver.gameserver.network.serverpackets import ItemList
from com.l2jserver.util import Rnd

class MergeEnchance(JQuest):
	qID = -1				#quest id �w�]��
	qn = "mergeEnchant"		#quest �W�� �w�]��
	qDesc = "custom"		#quest �y�z �w�]��
	
	NPCID = 100				#Ĳ�o���Ȫ� NPC
	
	htm_header = "<html><body><title>�X���j��</title>"
	htm_footer = "</body></html>"
	htm_select_part = """��n�j�ƪ����~�˳Ʀn, ��ܭn�j�ƪ�����<BR>
	<a action="bypass -h Quest %(qn)s head">�Y��</a><BR1>
	<a action="bypass -h Quest %(qn)s fullarmor">�W�U�s����</a><BR1>
	<a action="bypass -h Quest %(qn)s chest">�W����</a><BR1>
	<a action="bypass -h Quest %(qn)s legs">�U����</a><BR1>
	<a action="bypass -h Quest %(qn)s gloves">��M��</a><BR1>
	<a action="bypass -h Quest %(qn)s feet">�c��</a><BR1>
	<a action="bypass -h Quest %(qn)s rhand">���Z��</a><BR1>
	<a action="bypass -h Quest %(qn)s lrhand">����Z��</a><BR1>
	<a action="bypass -h Quest %(qn)s lhand">��/����</a><BR1>
	"""
	htm_show_2nd_item = """<a action="bypass -h Quest %(qn)s %(tmp)s">%(tmp2)s</a><BR>"""
	
	bodypart = {
		"head":ItemTable._slots.get("head")
		,"fullarmor":ItemTable._slots.get("fullarmor")
		,"chest":ItemTable._slots.get("chest")
		,"legs":ItemTable._slots.get("legs")
		,"gloves":ItemTable._slots.get("gloves")
		,"feet":ItemTable._slots.get("feet")
		,"lhand":ItemTable._slots.get("lhand")
		,"rhand":ItemTable._slots.get("rhand")
		,"lrhand":ItemTable._slots.get("lrhand")
	}

	def firstpage(self, **kv):
		return self.htm_header + self.htm_select_part + self.htm_footer

	def __init__(self, id = qID, name = qn, descr = qDesc):
		self.qID, self.qn, self.qDesc = id, name, descr
		JQuest.__init__(self, id, name, descr)
		self.addStartNpc(self.NPCID)
		self.addFirstTalkId(self.NPCID)
		self.addTalkId(self.NPCID)
		self.htm_select_part = self.htm_select_part % {"qn":self.qn}
		self.htm_show_2nd_item = self.htm_show_2nd_item % {"qn":self.qn, "tmp":"%d_%d", "tmp2":"%s"}
		print "Init:" + self.qn + " loaded"

	def getEquItem(self, player, bodypart):
		return [x for x in player.getInventory().getItems() if x.getLocation() == ItemLocation.PAPERDOLL and x.getItem().getBodyPart() == bodypart]
		
	def getInvItemById(self, player, item_id):
		return [x for x in player.getInventory().getItems() if x.getLocation() == ItemLocation.INVENTORY and x.getItemId() == item_id]
	
	def check(self, player, item1, item2):
		if not item1: return False
		if not item2: return False
		if item1.getOwnerId() != player.getObjectId():return False
		if item2.getOwnerId() != player.getObjectId():return False
		if not item1.isEnchantable(): return False
		return True
		
	def merge(self, player, item1, item2):
		inv = player.getInventory()
		item1 = inv.getItemByObjectId(int(item1))
		item2 = inv.getItemByObjectId(int(item2))
		if not self.check(player, item1, item2):
			return self.htm_header + "���w���D��X���D<BR>�нT�w�D���j��" + self.htm_footer
		enchant2 = item2.getEnchantLevel()
		inv.destroyItem(self.qn, item2, player, item2)
		item1.setEnchantLevel(item1.getEnchantLevel()+Rnd.get(enchant2+1))
		item1.updateDatabase()
		player.sendPacket(EnchantResult(0, 0, 0))
		sm = SystemMessage.getSystemMessage(SystemMessageId.C1_SUCCESSFULY_ENCHANTED_A_S2_S3);
		sm.addCharName(player)
		sm.addNumber(item1.getEnchantLevel())
		sm.addItemName(item1)
		player.sendPacket(sm)		
		su = StatusUpdate(player)
		su.addAttribute(StatusUpdate.CUR_LOAD, player.getCurrentLoad())
		player.sendPacket(su)
		player.sendPacket(ItemList(player, False));
		player.broadcastUserInfo()
		return self.htm_header + "����! �X���j�Ʀ��\<BR>"+ self.htm_select_part + self.htm_footer
		
	def onAdvEvent(self, event, npc, player):
		if event in self.bodypart:
			frist_item = self.getEquItem(player, self.bodypart[event])
			if len(frist_item):
				r = "�N�n�j�ƪ��D��:%s +%d<BR>" % (frist_item[0].getItemName(), frist_item[0].getEnchantLevel())
				items = self.getInvItemById(player, frist_item[0].getItemId())
				if len(items):
					r += "�I�]�����H�U�묹�D��i�@���X������.<BR1>�X�����ܪ��묹�D��|����<BR1>�X���᪺�j�Ƶ��� = �˳ƹD��j�Ƶ��� + �H����<BR1> �H���� = 0 �� (�묹�D��j�Ƶ���)<BR1>�ҥH�O�� +0 ���ӦX����<BR>"
					for item in items:
						r += self.htm_show_2nd_item % (frist_item[0].getObjectId(), item.getObjectId(), "%s +%d" % (item.getItemName(), item.getEnchantLevel()))
				else:
					r += "�I�]���S���ۦP���D��@���X���j�Ƥ���"
				return self.htm_header + r + self.htm_footer
			return self.htm_header + "�Х��˳ƭn�j�ƪ��D��" + self.htm_footer
		else:
			item1, item2 = event.split("_")
			return self.merge(player, item1, item2)
			
		
	def onFirstTalk(self, npc, player):
		return self.firstpage()
		
MergeEnchance()
