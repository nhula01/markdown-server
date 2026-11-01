"""Small schematic ink illustrations for topic and chapter headings."""
from html import escape
import math


def wave(y, amplitude=28, phase=0):
    points = [(x, y - amplitude * math.sin((x-25)/46 + phase)) for x in range(25, 336, 3)]
    return '<path class="art-wave" d="M' + ' L'.join(f'{x},{v:.1f}' for x,v in points) + '"/>'


def label(x, y, text):
    return f'<text x="{x}" y="{y}" class="art-label">{escape(text)}</text>'


def diagram(topic, title=''):
    if not topic and title not in {'Draft', 'Science of Review'}:
        return ''
    slug = topic['slug'] if topic else 'draft'
    key = slug
    explicit = {'Phonons':'phonons', 'Plasmons':'plasmons', 'Plasmonics':'surface-wave', 'Foundations of SLH':'slh', 'Duan Kimble':'cavity-phase', 'Coherent State':'mode-basis', 'Science of Review':'recall'}
    if title in explicit:
        key = explicit[title]
    elif title == 'Quantum Pictures':
        key = 'quantum-pictures'
    elif title == 'Polaritons':
        key = 'polaritons'
    elif title == 'Draft':
        key = 'draft'
    elif title == 'Electrons in Crystals':
        key = 'bands'
    elif title == 'Crystal':
        key = 'lattice'
    elif title == 'Oscillator Model':
        key = 'oscillator'
    elif title == 'Linear Light':
        key = 'response'
    elif title == "Maxwell's Equations":
        key = 'field'
    descriptions = {
        'phonons': 'Atoms coupled by restoring forces support collective lattice vibrations.',
        'plasmons': 'Longitudinal electron-density modulation creates a restoring electric field.',
        'surface-wave': 'A surface plasmon polariton travels along an interface with fields decaying away from it.',
        'slh': 'Modular quantum components described by S, L and H connect through a propagating field.',
        'cavity-phase': 'An atom inside a one-sided cavity changes the reflection phase of a photon.',
        'mode-basis': 'Distinct optical modes form a basis for describing the electromagnetic field.',
        'recall': 'An activator links an idea to recall, checking, and a later return.',
        'quantum-pictures': 'Schrödinger and Heisenberg pictures assign time evolution to the state or the operator while preserving the same expectation value.',
        'polaritons': 'Coupled light and material modes split into upper and lower polariton branches.',
        'draft': 'A blank quiz card awaiting questions.',
        'fields-and-waves': 'Two field components sharing a wave: electric and magnetic fields.',
        'field': 'Field lines spreading from a positive charge and converging on a negative charge.',
        'light-and-matter': 'An incident field drives a bound charge, producing a material response.',
        'oscillator': 'A driven bound charge modeled as a mass on a spring.',
        'response': 'An incoming wave meets matter and emerges with a changed phase.',
        'bands': 'Electronic energy bands arise from states in a periodic crystal.',
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
    if key == 'phonons':
        for i,x in enumerate((55,115,175,235,295)):
            art += f'<circle cx="{x}" cy="105" r="10"/>'
            if i<4: art += f'<path d="M{x+10} 105h5l5-8 8 16 8-16 8 16 6-8"/>'
            dx=15 if i%2==0 else -15
            art += f'<path class="art-secondary" d="M{x-dx} 68h{dx*2}m{-5 if dx>0 else 5}-4 {5 if dx>0 else -5} 4 {-5 if dx>0 else 5} 4"/>'
        art += label(80,172,'collective displacement')
    elif key == 'plasmons':
        for x in (35,48,62,80,110,145,160,173,185,199,225,257,285,300,313):
            art += f'<circle cx="{x}" cy="90" r="3"/>'
        art += '<g class="art-secondary">'+wave(135,18)+'</g><path d="M115 53h70m-7-4 7 4-7 4"/>'+label(124,40,'E ∥ k')+label(80,195,'electron-density wave')
    elif key == 'surface-wave':
        art = '<path class="art-axis" d="M25 112H335"/>'+label(28,48,'dielectric')+label(28,190,'metal')
        for y,a in ((78,13),(100,24),(130,15),(150,6)):
            art += '<g class="art-secondary">'+wave(y,a)+'</g>'
        art += '<path d="M255 39h60m-7-4 7 4-7 4"/>'+label(207,25,'along surface')
    elif key == 'slh':
        art = '<rect x="50" y="60" width="95" height="80" rx="5"/><rect x="210" y="60" width="95" height="80" rx="5"/><path class="art-secondary" d="M15 100h35m95 0h65m-7-4 7 4-7 4m102 0h33"/>'+label(67,107,'S, L, H')+label(228,107,'S, L, H')+label(83,186,'connect the components')
    elif key == 'cavity-phase':
        art = '<path d="M135 55V155M235 55V155"/><path class="art-secondary" d="M128 55V155M242 55V155"/><circle cx="185" cy="105" r="9"/><path d="M25 85h95m-7-4 7 4-7 4M120 125H25m7-4-7 4 7 4"/>'+label(37,67,'in')+label(28,151,'reflected')+label(170,88,'atom')+label(82,197,'state → reflection phase')
    elif key == 'mode-basis':
        art = '<path class="art-axis" d="M50 70H320M50 145H320"/>'
        for y,freq in ((70,1),(145,2)):
            points=[f'{x},{y-22*math.sin((x-50)/270*2*math.pi*freq):.1f}' for x in range(50,321,3)]
            art += '<path class="art-secondary" d="M'+' L'.join(points)+'"/>'
        art += label(18,75,'φ₁')+label(18,150,'φ₂')+label(82,201,'a basis for the field')
    elif key == 'recall':
        art = '<circle cx="175" cy="100" r="31"/><path class="art-secondary" d="M50 100h94M206 100h104m-7-4 7 4-7 4M300 123C265 192 85 192 50 123m0 8v-8h8"/>'+label(150,105,'idea')+label(24,78,'activator')+label(264,78,'recall')+label(130,198,'check & return')
    elif key == 'quantum-pictures':
        for x in (90, 270):
            art += f'<circle class="art-axis" cx="{x}" cy="92" r="40" stroke-dasharray="3 5"/><path class="art-axis" d="M{x-49} 92H{x+49}M{x} 43V141"/>'
        art += '<path class="art-secondary" d="M90 92 119 64m-9 2 9-2-2 9M270 92 299 64m-9 2 9-2-2 9"/>'
        art += label(43,28,'Schrödinger') + label(225,28,'Heisenberg')
        art += label(55,160,'state moves') + label(222,160,'operator moves')
        art += label(169,98,'=') + label(66,204,'same measurement: ⟨A⟩')
    elif key == 'polaritons':
        art = '<path class="art-axis" d="M40 175H325M50 185V25"/><path class="art-axis" stroke-dasharray="4 5" d="M65 145 310 47M65 100H310"/>'
        for sign in (-1,1):
            points=[]
            for x in range(65,311,3):
                detune=(x-180)*.4
                y=100-detune/2+sign*math.sqrt((detune/2)**2+18**2)
                points.append(f'{x},{y:.1f}')
            art += '<path class="art-secondary" d="M'+' L'.join(points)+'"/>'
        art += label(24,31,'ω')+label(312,196,'k')+label(260,30,'upper')+label(260,145,'lower')
    elif key == 'draft':
        art = '<path class="art-axis" d="M105 25H230L255 50V190H105Z"/><path d="M230 25V50H255"/>'+label(145,65,'quiz')+'<text x="166" y="132" class="art-label" style="font-size:42px">?</text>'
    elif key == 'fields-and-waves':
        art = '<path class="art-axis" d="M20 105H340"/>' + wave(93, 30) + '<g class="art-secondary">' + wave(127, 22) + '</g>' + label(28,52,'E') + label(28,166,'B') + '<path d="M270 185h55m-8-5 8 5-8 5"/>' + label(190,190,'propagation')
    elif key == 'field':
        for y in (35,65,145,175):
            art += f'<path d="M85 105C140 {y} 220 {y} 275 105"/>'
        art += '<path d="M85 105H275m-95-5 8 5-8 5"/><circle cx="85" cy="105" r="17"/><circle cx="275" cy="105" r="17"/>' + label(80,110,'+') + label(270,110,'−') + label(130,195,'field & sources')
    elif key in {'light-and-matter','oscillator'}:
        art = '<path class="art-axis" d="M60 50V150M48 55l12-5m-12 25 12-5m-12 25 12-5m-12 25 12-5m-12 25 12-5"/><path d="M60 100h20l10-18 18 36 18-36 18 36 18-36 18 36 10-18h22"/><circle cx="229" cy="100" r="17"/><path class="art-secondary" d="M265 100h63m-8-5 8 5-8 5"/>' + label(206,151,'charge') + label(264,75,'drive') + label(90,191,'motion → response')
    elif key == 'response':
        art = wave(105,26) + '<path class="art-secondary" d="M142 35V173M219 35V173"/><path class="art-axis" d="M143 173h75"/>' + label(154,194,'matter')
    elif key == 'bands':
        art = '<path class="art-axis" d="M35 170H330M45 185V25"/><path d="M60 58Q180 155 315 58M60 150Q180 53 315 150"/>' + label(20,33,'E') + label(315,191,'k')
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
