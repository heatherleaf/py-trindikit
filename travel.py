# -*- encoding: utf-8 -*-

from ibis import *

preds0 = 'return', 'need-visa'

preds1 = {'price': 'int',
          'how': 'means',
          'dest_city': 'city',
          'depart_city': 'city',
          'depart_day': 'day',
          'class': 'flight_class',
          'return_day': 'day',
          }

means = 'plane', 'train'
cities = 'paris', 'london'
days = 'today', 'tomorrow'
classes = 'first', 'second'

sorts = {'means': means,
         'city': cities,
         'day': days,
         'flight_class': classes,
         }

domain = Domain(preds0, preds1, sorts)

whq = lambda pred: WHQ(Pred1(pred))
ynq = lambda pred: YNQ(Prop(Pred0(pred)))

price_plan = Plan(p("?x.price(x)"),
                  [Findout(p("?x.how(x)")),
                   Findout(p("?x.dest_city(x)")),
                   Findout(p("?x.depart_city(x)")),
                   Findout(p("?x.depart_day(x)")),
                   Findout(p("?x.class(x)")),
                   Findout(p("?return")),
                   If(p("?return"), 
                      [Findout(p("?x.return_day(x)"))]),
                   ConsultDB(p("?x.price(x)"))
                   ])


# Följande måste klaras av såsmåningom:
#
# contact_plan(change_contact_name, change, contact,
# 	     [],
# 	     [ findout(C^change_contact_new_name(C),
# 		       { type=text, default=change_contact_name, device=phone }),
# 	       dev_do(phone, 'ChangeContactName'),
# 	       forget(view_contact_name(_)),
# 	       forget(change_contact_name(_)),
# 	       if_then(change_contact_new_name(Name),
# 		       [ assume_shared(view_contact_name(Name)),
# 			 assume_shared(change_contact_name(Name)) ]),
# 	       forget(change_contact_new_name(_))
# 	     ]).
# postcond(change_contact_name, done('ChangeContactName')).
#
# OBS! if_then(..) binder en variabel Name som används i konsekvensen!
# Förslag:
#
#    If("change-contact-name(?x)", [assume_shared("view-contact-name(?x)"), ...])


class DomainTravel(Domain):
    def relevant(self, ans, que):
        return NotImplemented
    
    def resolves(self, prop, que):
        return NotImplemented
    
    def combine(self, que, ans):
        return NotImplemented
    
    def get_plan(self, que):
        return NotImplemented

class DatabaseTravel(Database):
    pass

class GrammarTravelEnglish(Grammar):
    pass



######################################################################
# Running the dialogue system
######################################################################

def run():
    domain = DomainTravel()
    database = DatabaseTravel()
    grammar = GrammarTravelEnglish()
    ibis = ibis.IBIS1(domain, database, grammar)
    ibis.run()

if __name__=='__main__':
    run()
