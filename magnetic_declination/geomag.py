# -*- coding: utf-8 -*-
"""
Pure Python implementation of the World Magnetic Model (WMM-2025).
Adapted from the pygeomag library.
"""

import math

class GeoMagResult:
    """Stores the calculated magnetic values for a given coordinate and time."""
    def __init__(self, time: float, alt: float, glat: float, glon: float) -> None:
        self.time = time
        self.alt = alt
        self.glat = glat
        self.glon = glon
        self.x = None  # North Component (nT)
        self.y = None  # East Component (nT)
        self.z = None  # Vertical Component (nT)
        self.h = None  # Horizontal Intensity (nT)
        self.f = None  # Total Intensity (nT)
        self.i = None  # Inclination (degrees)
        self.d = None  # Declination / Magnetic Variation (degrees)

    @property
    def dec(self) -> float:
        return self.d

    @property
    def inclination(self) -> float:
        return self.i

    @property
    def total_intensity(self) -> float:
        return self.f


class GeoMag:
    """World Magnetic Model calculation engine."""
    def __init__(self, coefficients_data=None) -> None:
        if coefficients_data is None:
            from .wmm_2025 import WMM_2025
            coefficients_data = WMM_2025
        self._coefficients_data = coefficients_data
        self._maxord = 12
        self._size = self._maxord + 1
        self._epoch = None
        self._model = None
        self._release_date = None
        self._c = None
        self._cd = None
        self._p = None
        self._fn = None
        self._fm = None
        self._k = None
        self._load_coefficients()

    def _load_coefficients(self) -> None:
        c = [[0.0 for _ in range(self._size)] for _ in range(self._size)]
        cd = [[0.0 for _ in range(self._size)] for _ in range(self._size)]
        snorm = [0.0] * (self._size**2)
        fn = [0.0] * self._size
        fm = [0.0] * self._size
        k = [[0.0 for _ in range(self._size)] for _ in range(self._size)]

        (epoch, model, release_date), coefficients = self._coefficients_data

        c[0][0] = 0.0
        cd[0][0] = 0.0

        for n, m, gnm, hnm, dgnm, dhnm in coefficients:
            if m > self._maxord:
                break
            if m > n or m < 0:
                raise ValueError("Corrupt coefficients data")
            if m <= n:
                c[m][n] = gnm
                cd[m][n] = dgnm
                if m != 0:
                    c[n][m - 1] = hnm
                    cd[n][m - 1] = dhnm

        snorm[0] = 1.0
        fm[0] = 0.0
        for n in range(1, self._maxord + 1):
            snorm[n] = snorm[n - 1] * float(2 * n - 1) / float(n)
            j = 2
            m = 0
            D1 = 1
            D2 = (n - m + D1) / D1
            while D2 > 0:
                k[m][n] = float(((n - 1) * (n - 1)) - (m * m)) / float(
                    (2 * n - 1) * (2 * n - 3)
                )
                if m > 0:
                    flnmj = float((n - m + 1) * j) / float(n + m)
                    snorm[n + m * self._size] = snorm[
                        n + (m - 1) * self._size
                    ] * math.sqrt(flnmj)
                    j = 1
                    c[n][m - 1] = snorm[n + m * self._size] * c[n][m - 1]
                    cd[n][m - 1] = snorm[n + m * self._size] * cd[n][m - 1]
                c[m][n] = snorm[n + m * self._size] * c[m][n]
                cd[m][n] = snorm[n + m * self._size] * cd[m][n]
                D2 -= 1
                m += D1
            fn[n] = float(n + 1)
            fm[n] = float(n)
        k[1][1] = 0.0

        self._epoch = epoch
        self._model = model
        self._release_date = release_date
        self._c = c
        self._cd = cd
        self._p = snorm
        self._fn = fn
        self._fm = fm
        self._k = k

    def calculate(
        self,
        glat: float,
        glon: float,
        alt: float,
        time: float,
        allow_date_outside_lifespan: bool = True,
    ) -> GeoMagResult:
        """Calculates geomagnetic field components for a location/date.
        
        :param glat: Latitude in decimal degrees (-90 to 90, North positive)
        :param glon: Longitude in decimal degrees (-180 to 180, East positive)
        :param alt: Altitude in kilometers relative to ellipsoid
        :param time: Decimal year (e.g. 2026.41)
        """
        tc = [[0.0 for _ in range(self._size)] for _ in range(self._size)]
        dp = [[0.0 for _ in range(self._size)] for _ in range(self._size)]
        sp = [0.0] * self._size
        cp = [0.0] * self._size
        pp = [0.0] * self._size

        sp[0] = 0.0
        cp[0] = pp[0] = 1.0
        dp[0][0] = 0.0
        a = 6378.137
        b = 6356.7523142
        re = 6371.2
        a2 = a * a
        b2 = b * b
        c2 = a2 - b2
        a4 = a2 * a2
        b4 = b2 * b2
        c4 = a4 - b4

        dt = time - self._epoch
        if (dt < 0.0 or dt > 5.0) and not allow_date_outside_lifespan:
            raise ValueError("Time extends beyond WMM model life span (2025.0 - 2030.0)")

        rlon = math.radians(glon)
        rlat = math.radians(glat)
        srlon = math.sin(rlon)
        srlat = math.sin(rlat)
        crlon = math.cos(rlon)
        crlat = math.cos(rlat)
        srlat2 = srlat * srlat
        crlat2 = crlat * crlat
        sp[1] = srlon
        cp[1] = crlon

        # Convert geodetic coordinates to spherical
        q = math.sqrt(a2 - c2 * srlat2)
        q1 = alt * q
        q2 = ((q1 + a2) / (q1 + b2)) * ((q1 + a2) / (q1 + b2))
        ct = srlat / math.sqrt(q2 * crlat2 + srlat2)
        st = math.sqrt(1.0 - (ct * ct))
        r2 = (alt * alt) + 2.0 * q1 + (a4 - c4 * srlat2) / (q * q)
        r = math.sqrt(r2)
        d = math.sqrt(a2 * crlat2 + b2 * srlat2)
        ca = (alt + d) / r
        sa = c2 * crlat * srlat / (r * d)

        for m in range(2, self._maxord + 1):
            sp[m] = sp[1] * cp[m - 1] + cp[1] * sp[m - 1]
            cp[m] = cp[1] * cp[m - 1] - sp[1] * sp[m - 1]

        aor = re / r
        ar = aor * aor
        bt = bp = br = bpp = 0.0

        for n in range(1, self._maxord + 1):
            ar = ar * aor
            m = 0
            D3 = 1
            D4 = (n + m + D3) // D3
            while D4 > 0:
                if n == m:
                    self._p[n + m * self._size] = (
                        st * self._p[n - 1 + (m - 1) * self._size]
                    )
                    dp[m][n] = (
                        st * dp[m - 1][n - 1]
                        + ct * self._p[n - 1 + (m - 1) * self._size]
                    )
                elif n == 1 and m == 0:
                    self._p[n + m * self._size] = (
                        ct * self._p[n - 1 + m * self._size]
                    )
                    dp[m][n] = (
                        ct * dp[m][n - 1] - st * self._p[n - 1 + m * self._size]
                    )
                elif n > 1 and n != m:
                    if m > n - 2:
                        self._p[n - 2 + m * self._size] = 0.0
                    if m > n - 2:
                        dp[m][n - 2] = 0.0
                    self._p[n + m * self._size] = (
                        ct * self._p[n - 1 + m * self._size]
                        - self._k[m][n] * self._p[n - 2 + m * self._size]
                    )
                    dp[m][n] = (
                        ct * dp[m][n - 1]
                        - st * self._p[n - 1 + m * self._size]
                        - self._k[m][n] * dp[m][n - 2]
                    )

                # Time adjust gauss coefficients
                tc[m][n] = self._c[m][n] + dt * self._cd[m][n]
                if m != 0:
                    tc[n][m - 1] = self._c[n][m - 1] + dt * self._cd[n][m - 1]

                par = ar * self._p[n + m * self._size]
                if m == 0:
                    temp1 = tc[m][n] * cp[m]
                    temp2 = tc[m][n] * sp[m]
                else:
                    temp1 = tc[m][n] * cp[m] + tc[n][m - 1] * sp[m]
                    temp2 = tc[m][n] * sp[m] - tc[n][m - 1] * cp[m]
                bt = bt - ar * temp1 * dp[m][n]
                bp += self._fm[m] * temp2 * par
                br += self._fn[n] * temp1 * par

                # Special case for geographic poles
                if st == 0.0 and m == 1:
                    if n == 1:
                        pp[n] = pp[n - 1]
                    else:
                        pp[n] = ct * pp[n - 1] - self._k[m][n] * pp[n - 2]
                    parp = ar * pp[n]
                    bpp += self._fm[m] * temp2 * parp

                D4 -= 1
                m += D3

        if st == 0.0:
            bp = bpp
        else:
            bp /= st

        # Rotate components spherical -> geodetic
        bx = -bt * ca - br * sa
        by = bp
        bz = bt * sa - br * ca

        result = GeoMagResult(time, alt, glat, glon)

        # Compute field components
        bh = math.sqrt((bx * bx) + (by * by))
        result.f = math.sqrt((bh * bh) + (bz * bz))
        result.d = math.degrees(math.atan2(by, bx))
        result.i = math.degrees(math.atan2(bz, bh))
        result.h = bh
        result.x = bx
        result.y = by
        result.z = bz

        return result
