#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Orbit description
"""

import numpy as np

from .forms import FormTransform
from .ephem import Ephem
from ..utils import Date
from ..frames.frame import get_frame, orbit2frame
from ..propagators import get_propagator


class Orbit(np.ndarray):
    """Coordinate representation
    """

    def __new__(cls, date, coord, form, frame, propagator, **kwargs):
        """
        Args:
            date (Date): Date associated with the state vector
            coord (list): 6-length state vector
            form (str): Name of the form of the state vector
            frame (str): Name of the frame of reference of the state vector
            propagator (str): Name of the propagator to be used to extrapolate
        """

        if len(coord) != 6:
            raise ValueError("Should be 6 in length")

        if isinstance(form, str):
            form = FormTransform._tree[form]
        elif form.name not in FormTransform._tree:
            raise ValueError("Unknown form '{}'".format(form))

        if isinstance(frame, str):
            frame = get_frame(frame)

        if isinstance(propagator, str):
            propagator = get_propagator(propagator)

        obj = np.ndarray.__new__(cls, (6,), buffer=np.array(coord), dtype=float)
        obj.date = date
        obj._form = form
        obj._frame = frame
        obj.propagator = propagator
        obj.complements = kwargs

        return obj

    def copy(self, *, frame=None, form=None):
        """Override :py:meth:`numpy.ndarray.copy()` to include additional
        fields
        """
        new_obj = self.__class__(
            self.date, self.base.copy(), self.form,
            self.frame, self.propagator, **self.complements)
        if frame and frame != self.frame:
            new_obj.frame = frame
        if form and form != self.form:
            new_obj.form = form
        return new_obj

    @property
    def names(self):
        """Gives the names of the fields
        """
        return self.form.param_names

    def __getattr__(self, name):

        convert = {
            'theta': 'θ',
            'phi': 'φ',
            'Omega': "Ω",
            'omega': 'ω',
            'nu': "ν",
            'theta_dot': 'θ_dot',
            'phi_dot': 'φ_dot',
        }

        # Conversion of variable name to utf-8
        if name in convert:
            name = convert[name]

        # Verification if the variable is available in the current form
        if name not in self.names:
            raise AttributeError("'{}' object has no attribute {!r}".format(self.__class__, name))

        i = self.names.index(name)
        return self[i]

    def __getitem__(self, key):

        if isinstance(key, (int, slice)):
            return super().__getitem__(key)
        else:
            try:
                return self.__getattr__(key)
            except AttributeError as err:
                raise KeyError(str(err))

    def __repr__(self):  # pragma: no cover
        coord_str = '\n'.join(
            [" " * 4 + "%s = %s" % (name, arg) for name, arg in zip(self.names, self)]
        )

        propagator = self.propagator.__name__ if self.propagator is not None else self.propagator

        fmt = "Orbit =\n  date = {date}\n  form = {form}\n  frame = {frame}\n  propag = {propag}\n  coord =\n{coord}".format(
            date=self.date,
            coord=coord_str,
            form=self.form,
            frame=self.frame,
            propag=propagator
        )
        return fmt

    @property
    def form(self):
        return self._form

    @form.setter
    def form(self, new_form):
        """Changes the form of the coordinates in-place

        Args:
            new_form (str or Form)
        """
        if isinstance(new_form, str):
            new_form = FormTransform._tree[new_form]

        fmt = FormTransform(self)
        self.base.setfield(fmt.transform(new_form), dtype=float)
        self._form = new_form

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, new_frame):
        """Convert the orbit to a new frame of reference

        Args:
            new_frame (str or Frame)
        """
        old_form = self.form

        if isinstance(new_frame, str):
            new_frame = get_frame(new_frame)

        if new_frame != self.frame:
            self.form = 'cartesian'
            try:
                new_coord = self.frame(self.date, self).transform(new_frame.name)
                self.base.setfield(new_coord, dtype=float)
                self._frame = new_frame
            finally:
                self.form = old_form

    def propagate(self, date):
        """Propagate the orbit to a new date

        Args:
            date (Date)
        Return:
            Orbit
        """

        if type(self.propagator) is type:
            # Instanciation of the propagator, only the first time the propagator
            # is called
            self.propagator = self.propagator(self)

        return self.propagator.propagate(date)

    def ephemeris(self, start, stop, step):
        """Generator giving the propagation of the orbit at different dates

        Args:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Yield:
            Orbit
        """

        for date in Date.range(start, stop, step, inclusive=True):
            yield self.propagate(date)

    def ephem(self, *args):
        """
        Args:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Return:
            Ephem:
        """
        return Ephem(self.ephemeris(*args))

    def register_as_frame(self, name, orientation=None):  # pragma: no cover
        """Register the orbit as frame.

        see :py:func:`space.frames.frame.orbit2frame` for details of the arguments
        """
        orbit2frame(name, self, orientation)
