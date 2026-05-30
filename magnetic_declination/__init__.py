# -*- coding: utf-8 -*-

def classFactory(iface):
    """Entry point called by QGIS to instantiate the plugin.
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .magnetic_declination_plugin import MagneticDeclinationPlugin
    return MagneticDeclinationPlugin(iface)
