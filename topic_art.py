"""Small schematic ink illustrations for topic and chapter headings."""
from html import escape
import math


def wave(y, amplitude=28, phase=0):
    points = [(x, y - amplitude * math.sin((x-25)/46 + phase)) for x in range(25, 336, 3)]
    return '<path class="art-wave" d="M' + ' L'.join(f'{x},{v:.1f}' for x,v in points) + '"/>'


def label(x, y, text):
    return f'<text x="{x}" y="{y}" class="art-label">{escape(text)}</text>'


def diagram(topic, title=''):
    if not topic:
        return ''
    slug = topic['slug']
    key = slug
    if title in {'Crystal', 'Electrons in Crystals'}:
        key = 'lattice'
    elif title == 'Oscillator Model':
        key = 'oscillator'
    elif title == 'Linear Light':
        key = 'response'
    elif title == "Maxwell's Equations":
        key = 'field'
    descriptions = {
        'fields-and-waves': 'Two field components sharing a wave: electric and magnetic fields.',
        'field': 'Field lines spreading from a positive charge and converging on a negative charge.',
        'light-and-matter': 'An incident field drives a bound charge, producing a material response.',
        'oscillator': 'A driven bound charge modeled as a mass on a spring.',
        'response': 'An incoming wave meets matter and emerges with a changed phase.',
        'lattice': 'A periodic crystal lattice with a delocalized electronic wave.',
        'quantum-optics': 'A coherent state represented by a minimum-uncertainty region in quadrature space.',
        'open-quantum-systems': 'A quantum system exchanges energy and information with its environment.',
        'quantum-networks': 'Connected quantum systems exchange signals through a waveguide.',
        'quantum-information': 'A Bloch sphere representing the states of a qubit.',
        'nonlinear-and-fiber-optics': 'A pulse traveling through a waveguide.',
        'learning-and-reservoirs': 'An input drives a recurrent physical reservoir and produces an output.',
        'mathematical-methods': 'The area beneath a curve represents its integral.',
    }
    art = ''
    if key == 'fields-and-waves':
        art = '<path class="art-axis" d="M20 105H340"/>' + wave(93, 30) + '<g class="art-secondary">' + wave(127, 22) + '</g>' + label(28,52,'E') + label(28,166,'B') + '<path d="M270 185h55m-8-5 8 5-8 5"/>' + label(190,190,'propagation')
    elif key == 'field':
        for y in (35,65,145,175):
            art += f'<path d="M85 105C140 {y} 220 {y} 275 105"/>'
        art += '<path d="M85 105H275m-95-5 8 5-8 5"/><circle cx="85" cy="105" r="17"/><circle cx="275" cy="105" r="17"/>' + label(80,110,'+') + label(270,110,'−') + label(130,195,'field & sources')
    elif key in {'light-and-matter','oscillator'}:
        art = '<path class="art-axis" d="M60 50V150M48 55l12-5m-12 25 12-5m-12 25 12-5m-12 25 12-5m-12 25 12-5"/><path d="M60 100h20l10-18 18 36 18-36 18 36 18-36 18 36 10-18h22"/><circle cx="229" cy="100" r="17"/><path class="art-secondary" d="M265 100h63m-8-5 8 5-8 5"/>' + label(206,151,'charge') + label(264,75,'drive') + label(90,191,'motion → response')
    elif key == 'response':
        art = wave(105,26) + '<path class="art-secondary" d="M142 35V173M219 35V173"/><path class="art-axis" d="M143 173h75"/>' + label(154,194,'matter')
    elif key == 'lattice':
        for x in (55,115,175,235,295):
            for y in (55,105,155):
                art += f'<circle cx="{x}" cy="{y}" r="5"/>'
        art += '<g class="art-secondary">' + wave(105,21) + '</g>' + label(90,196,'periodicity & waves')
    elif key == 'quantum-optics':
        art = '<path class="art-axis" d="M45 160H310M80 190V25"/><ellipse cx="195" cy="91" rx="34" ry="34"/><path class="art-secondary" d="M80 160 195 91"/><circle cx="195" cy="91" r="3"/>' + label(310,178,'q') + label(62,30,'p') + label(222,71,'α')
    elif key == 'open-quantum-systems':
        art = '<ellipse class="art-axis" cx="178" cy="108" rx="141" ry="70"/><circle cx="178" cy="108" r="31"/>' + label(167,114,'ρ')
        for x,y in ((65,70),(295,70),(65,148),(295,148)):
            art += f'<circle cx="{x}" cy="{y}" r="5"/><path class="art-secondary" d="M{x} {y} 178 108"/>'
        art += label(129,199,'environment')
    elif key in {'quantum-networks','learning-and-reservoirs'}:
        for x,y in ((86,60),(85,145),(175,105),(258,60),(260,145)):
            art += f'<circle cx="{x}" cy="{y}" r="12"/>'
        art += '<path class="art-secondary" d="M98 60 163 105 98 145M187 105 246 60M187 105 248 145M86 72V133M258 72V133"/><path d="M20 105h42m237 0h40"/>' + label(24,190,'input') + label(265,190,'output')
    elif key == 'quantum-information':
        art = '<circle cx="178" cy="104" r="67"/><ellipse class="art-axis" cx="178" cy="104" rx="67" ry="23"/><path class="art-axis" d="M178 20V185M90 104h177"/><path class="art-secondary" d="M178 104 212 52m-8 3 8-3-1 9"/>' + label(166,16,'|0⟩') + label(166,204,'|1⟩') + label(220,52,'ψ')
    elif key == 'nonlinear-and-fiber-optics':
        art = '<path class="art-axis" d="M25 65H335M25 150H335"/><path d="M25 107h95c22 0 26-54 52-54s27 54 52 54h111"/>' + label(133,192,'guided light')
    else:
        art = '<path class="art-axis" d="M35 165H335M45 180V25"/><path class="art-area" d="M45 165V133Q130 15 213 75T325 60V165Z"/><path d="M45 133Q130 15 213 75T325 60"/>' + label(309,189,'x') + label(18,38,'f(x)')
    return f'<figure class="topic-art"><svg viewBox="0 0 360 220" role="img" aria-label="{escape(descriptions[key],quote=True)}">{art}</svg></figure>'
