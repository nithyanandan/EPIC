#!/usr/bin/env python
import argparse
import numpy as np
from astropy.io import fits
from astropy import wcs
import astropy.units as u
from astropy.coordinates import SkyCoord

a = argparse.ArgumentParser(description='Take list of FITS files and derive '
                            'lightcurve for given sky coordinate.')
a.add_argument('--ra', metavar='ra', type=str, default='05:34:31.97',
               help='RA coordinate for source, in HH:MM:SS.SS format. Default is Crab.')
a.add_argument('--dec', metavar='dec', type=str, default='22:00:52.1',
               help='Dec coordinate for source, in DD:MM:SS.SS format. Default is Crab.')
a.add_argument('--equinox', metavar='equinox', type=str, default='J2000',
               help='Equinox for sky coordinates. Default is "J2000".')
a.add_argument('--npix', metavar='npix', type=float, default=0,
               help='Radius around central pixel to average, in units of pixels.')
a.add_argument('--outfile', metavar='outfile', type=str, default='lightcurve.npz',
               help='Output filename, default is lightcurve.npz')
a.add_argument('files', metavar='files', type=str, nargs='*', default=[],
               help='*.fits files to search for object.')
args = a.parse_args()

files = sorted(args.files)

target = SkyCoord(ra=args.ra, dec=args.dec, equinox=args.equinox, unit=(u.hourangle, u.deg), frame='fk5')
loc = np.array([[target.ra.deg, target.dec.deg, 0, 0, 0]])

lightcurve = []
times = []

for f in files:
    print('working on ' + f)
    hdulist = fits.open(f)
    for hdu in hdulist[1:]:
        times.append(hdu.header['DATETIME'])
        w_obj = wcs.WCS(hdu.header)
        p0 = w_obj.all_world2pix(loc, 0)
        try:
            r2 = (x - p0[0][0])**2 + (y - p0[0][1])**2
        except NameError:
            x_ind = np.arange(hdu.header['NAXIS1'])
            y_ind = np.arange(hdu.header['NAXIS2'])
            x, y = np.meshgrid(y_ind, x_ind)
            r2 = (x - p0[0][0])**2 + (y - p0[0][1])**2
        inds = np.where(r2 <= args.npix**2)
        ind_real = np.ix_(np.array([0]), np.arange(hdu.header['NAXIS4']),
                          np.arange(hdu.header['NAXIS3']), np.array(inds[0]), np.array(inds[1]))
        ind_imag = np.ix_(np.array([1]), np.arange(hdu.header['NAXIS4']),
                          np.arange(hdu.header['NAXIS3']), np.array(inds[0]), np.array(inds[1]))
        # Value should have dimensions Npol, Nfreq
        value = np.nanmean(hdu.data[ind_real] + 1j * hdu.data[ind_imag], axis=(0, 3, 4))
        lightcurve.append(value)

times = np.array(times)
lightcurve = np.array(lightcurve)
np.savez(args.outfile, times=times, lightcurve=lightcurve)
