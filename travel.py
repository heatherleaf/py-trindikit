
from ibis import IBIS

class Travel(Domain):
    def relevant(self, ans, que):
        return NotImplemented
    
    def resolves(self, prop, que):
        return NotImplemented
    
    def combine(self, que, ans):
        return NotImplemented
    
    def get_plan(self, que):
        return NotImplemented

class DatabaseTravel:
    pass

class GrammarTravelEnglish:
    pass

def run():
    domain = DomainTravel()
    database = DatabaseTravel()
    grammar = GrammarTravelEnglish()
    
    dme = IBIS(domain, database, grammar)
    dme.run()

