import SecretHitler as sh

GPRandom = sh.GamePlayer(["Finlay", "Callum", "Gareth", "Lucas", "Ollie"], True, False, False)

GPRole = sh.GamePlayer(["Finlay", "Callum", "Gareth", "Lucas", "Ollie"], False, True, False)

GPIntelligentRole = sh.GamePlayer(["Finlay", "Callum", "Gareth", "Lucas", "Ollie"], False, False, True)

print("Win Stats")
print("---------")
print("Random")
GPRandom.getWinStats()
print("Role")
GPRole.getWinStats()
print("Intelligent")
GPIntelligentRole.getWinStats()

GPIntelligentRoleTest = sh.GamePlayer(["Finlay", "Callum", "Gareth", "Lucas", "Ollie", "Ailsa", "Jack", "Alice", "Bob", "Ben"], False, False, True)
GPIntelligentRoleTest.getWinStats()