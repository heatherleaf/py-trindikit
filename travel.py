# -*- encoding: utf-8 -*-

#
# travel.py
#
# The author or authors of this code dedicate any and all 
# copyright interest in this code to the public domain.


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

domain.add_plan("?x.price(x)",
               [Findout("?x.how(x)"),
                Findout("?x.dest_city(x)"),
                Findout("?x.depart_city(x)"),
                Findout("?x.depart_day(x)"),
                Findout("?x.class(x)"),
                 Findout("?return()"),
                 If("?return()", 
                    [Findout("?x.return_day(x)")]),
                 ConsultDB("?x.price(x)")
                 ])



database = Database()

grammar = Grammar()

ibis = IBIS1(domain, database, grammar)




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


######################################################################
# Running the dialogue system
######################################################################

if __name__=='__main__':
    ibis.run()
