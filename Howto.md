# How to do things with py-trindikit #

These are just some very quick notes on how to use py-trindikit.

## Example application ##

There is one example application, travel.py. Here is an example session:

```
$ python travel.py
...
S> Hello.
...
U> price
...
S> How do you want to travel?
...
U> plane
...
S> Where do you want to go?
...
U> london
...
S> From where are you leaving?
...
U> paris
...
S> When do you want to leave?
...
U> today
...
S> First or second class?
...
U> first
...
S> Do you want a return ticket?
...
U> yes
...
S> When do you want to return?
...
U> tomorrow
...
S> The price is 345.
...
```

## Building another IBIS application ##

To build an IBIS application, start with a copy of `travel.py`. Define the predicates, sorts and individuals for your domain. And add each plan you want to your domain. Create a database and a grammar, then the IBIS dialogue manager.

## Extending the IBIS dialogue manager ##

Import everything from `ibis.py`. Create a new class subclassing `IBIS1`. Override the methods you need:
  * If you want to change the infostate, override `init_IS(self)`, and perhaps `print_IS(self, prefix)`.
  * If you want another control algorithm, override `control(self)`.
  * If you want different update or select algorithms, override `update(self)` and `select(self)`.
  * You can also override the IBIS1 update groups: `grounding`, `integrate`, `downdate_qud`, `load_plan`, `exec_plan`, `select_action`, `select_move`.
  * You can also add new update rules, see `ibis_rules.py` for examples and inspiration.

## Implementing a different dialogue theory ##

If you want to implement a completely different dialogue theory, e.g., the PTT theory, you only need the file `trindikit.py`.