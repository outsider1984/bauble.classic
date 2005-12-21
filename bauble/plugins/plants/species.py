#
# Species table definition
#
import os
import gtk
from sqlobject import *
import bauble.utils as utils
import bauble.paths as paths
from bauble.plugins import BaubleTable, tables, editors
from bauble.plugins.editor import TreeViewEditorDialog, ComboColumn, TextColumn
from bauble.utils.log import log, debug
#from speciesmeta import SpeciesMeta
    
#
# Species table
#
class Species(BaubleTable):
    
    def __init__(self, **kw):
        super(Species, self).__init__(**kw)
        
    sp_hybrid = EnumCol(enumValues=("H", 
                                    "x", 
                                    "+",
                                    ""), 
                        default="") 
    
    
    sp_qual = EnumCol(enumValues=("agg.", 
                                  "s.lat.", 
                                  "s. str.",
                                  ""), 
                      default="")
                                                    
    sp = StringCol(length=40, notNull=True)          # specific epithet
    sp_author = UnicodeCol(default=None)  # species author
        
    cv_group = StringCol(length=50, default=None)    # cultivar group
    #cv = StringCol(length=30, default=None)          # cultivar epithet
    #trades = StringCol(length=50, default=None)      # trades, e.g. "Sundance"
    
#    supfam = StringCol(length=30, default=None)          
#    subgen = StringCol(length=50, default=None)
#    subgen_rank = EnumCol(enumValues=("subgenus", 
#                                      "section", 
#                                      "subsection",
#                                      "series", 
#                                      "subseries",
#                                      None),
#                          default=None)                             

    isp = StringCol(length=30, default=None)         # intraspecific epithet
    isp_author = UnicodeCol(length=255, default=None) # intraspecific author
    # intraspecific rank
    isp_rank = EnumCol(enumValues=("subsp.", # subspecies
                                   "var.",   # variety
                                   "subvar.", # sub variety
                                   "f.",     # form
                                   "subf.",  # subform
                                   "cv.",    # cultivar                                   
                                   ""), 
                       default="")

#    isp2 = StringCol(length=30, default=None)
#    isp2_author = UnicodeCol(length=254, default=None)
#    isp2_rank = StringCol(length=10, default=None)
#
#
#    isp3 = StringCol(length=30, default=None)
#    isp3_author = UnicodeCol(length=254, default=None)
#    isp3_rank = StringCol(length=10, default=None)
#
#
#    isp4 = StringCol(length=30, default=None)
#    isp4_author = UnicodeCol(length=254, default=None)
#    isp4_rank = StringCol(length=10, default=None)
    

    # TODO: maybe the IUCN information should be looked up online
    # rather than being entered in the database or maybe there could
    # be an option to lookup the code online
    #iucn23 = StringCol(length=5, default=None)  # iucn category version 2.3
#    values["iucn23"] = [("EX", "Extinct"),
#                        ("EW", "Extinct in the wild"),
#                        ("CR", "Critically endangered"),
#                        ("EN", "Endangered"),
#                        ("VU", "Vulnerable"),
#                        #("LR", "Low risk"),
#                        ("CD", "Conservation dependent"), # low risk cat 1
#                        ("NT", "Near threatened"), # low risk cat 2
#                        ("LC", "Least consern"), # low risk cat 3
#                        ("DD", "Data deficient"),
#                        ("NE", "Not evaluated")]
    
    #iucn31 = StringCol(length=50, default=None) # iucn category_version 3.1
#    values["iucn31"] = [("EX", "Extinct"),
#                        ("EW", "Extinct in the wild"),
#                        ("CR", "Critically endangered"),
#                        ("EN", "Endangered"),
#                        ("VU", "Vulnerable"),
#                        ("NT", "Near threatened"), 
#                        ("LC", "Least consern"), 
#                        ("DD", "Data deficient"),
#                        ("NE", "Not evaluated")]
    
    #rank_qual = StringCol(length=1, default=None) # rank qualifier, a single
    # character
    
    id_qual = EnumCol(enumValues=("aff.", # Akin to or bordering
                                  "cf.", # compare with
                                  "Incorrect", # Incorrect
                                  "forsan", # Perhaps
                                  "near", # Close to
                                  "?", # Quesionable
                                  ""),
                      default="")
    
    # it would be best to display the vernacular names in a dropdown list
	# with a way to add to the list    
    vernacular_names = MultipleJoin('VernacularName', joinColumn='species_id')
    # this is the default vernacular name we'll use
    default_vernacular_name = ForeignKey('VernacularName', default=None, 
                                         cascade=True)
    
#    synonym = StringCol(default=None)  # should really be an id into table \
#                                       # or there should be a syn table
    
    # where this name stands in taxonomy, whether it's a synonym or
    # not basically, would probably be better to just leaves this and
    # look it up on www.ipni.org www.itis.usda.gov
    #taxonomic_status = StringCol()
    synonyms = MultipleJoin('SpeciesSynonym', joinColumn='species_id')
        
    # foreign keys and joins
    genus = ForeignKey('Genus', notNull=True, cascade=False)
    #accessions = MultipleJoin('Accessions', joinColumn='species_id')
    #images = MultipleJoin('Images', joinColumn='species_id')
    #references = MultipleJoin('Reference', joinColumn='species_id')
    
    notes = UnicodeCol(default=None)
    
    # hold meta information about this plant
    species_meta = SingleJoin('SpeciesMeta', joinColumn='species_id')        

    
    def __str__(self):
          #TODO: this needs alot of work to be complete
        #name = str(self.genus) + " " + self.sp
        #if self.isp_rank is not None:
        #    name = "%s %s %s" % (name, self.isp_rank, self.isp)
        #return name.strip()
        return Species.str(self)
    
    
    def markup(self, authors=False):
        return Species.str(self, authors, True)
    
    
    @staticmethod
    def str(species, authors=False, markup=False):
        """
        return the full plant name string
        NOTE: it may be better to create a separate method for the markup
        since substituting into the italic make slow things down, should do 
        some benchmarks. also, which is faster, doing substitution this way or
        by using concatenation
        """    
        # TODO: should do a translation table for any entities that might
        # be in the author strings ans use translate, what else besided 
        # ampersand could be in the author name
        if markup:
            italic = "<i>%s</i>"
        else:
            italic = "%s"
        #name = "%s %s" % (italic % str(species.genus), italic % species.sp)
        name = italic % str(species.genus)
        
        # take care of species hybrid
        if not species.sp_hybrid == "":
            # we don't have a second sp name for the hyrbid formula right now
            # so we'll just use the isp for now
            if species.isp is not None:
                name += " %s %s %s " % (italic % species.sp, 
                                        species.sp_hybrid,
                                        italic % species.isp)
            else:
                name += ' %s %s' % (species.sp_hybrid, species.sp)
        else:
            name += ' ' + italic % species.sp
            
        # cultivar groups and cultivars
        if species.cv_group is not None:
            if species.isp_rank == "cv.":
                name += ' (' + species.cv_group + " Group) '" + \
                italic % species.isp + "'"
            else: 
                name += ' ' + species.cv_group + ' Group'
            return name
        
        if species.sp_author is not None and authors is not False:
            name += ' ' + species.sp_author.replace('&', '&amp;')
        if not species.isp_rank == "":
            if species.isp_rank == "cv.":
                name += " '" + species.isp + "'"
            else:
                name += ' ' + species.isp_rank + ' ' + \
                              italic % species.isp
                if species.isp_author is not None and authors is not False:
                    name += ' ' + species.isp_author
        return name
    

    
class SpeciesSynonym(BaubleTable):
    # deleting either of the species this synonym refers to makes
    # this synonym irrelevant
    species = ForeignKey('Species', default=None, cascade=True)
    synonym = ForeignKey('Species', cascade=True)
    


class VernacularNameColumn(TextColumn):
        
	def __init__(self, tree_view_editor, header, so_col=None):
		super(VernacularNameColumn, self).__init__(tree_view_editor, header,
                                                   so_col=so_col)
		self.meta.editor = editors['VernacularNameEditor']
    
#    def on_key_press(self, widget, event, path):
#        """
#        if the column has an editor, invoke it
#        """
#        keyname = gtk.gdk.keyval_name(event.keyval)
#        if keyname == 'Return':
#            # start the editor for the cell if there is one
#            if self.meta.editor is not None:
#                model = self.table_editor.view.get_model()
#                it = model.get_iter(path)
#                row = model.get_value(it,0)
#                existing = select=row[self.name]
#                e = self.meta.editor(select=existing, 
#                                  connection=self.table_editor.transaction)
#                response = e.start()
#                if response == gtk.RESPONSE_ACCEPT or \
#                   response == gtk.RESPONSE_OK:
#                    committed = e.commit_changes(False)
#                    debug(committed)
#                    #if type(ret, list) or type(ret, tuple):                    
#                    self._set_view_model_value(path, (existing, committed))
#                    self.
#                    self.dirty = True
#                    self.renderer.emit('edited', path, committed)
#                e.destroy()
#	#def _get_name(self):
#	#	return 'default_vernacular_nameID'
#    #def _set_view_mode_values


# 
# the getter for the vernacular names column
#
def _get_vernacular_name(row):
    debug(row.default_vernacular_name)
    return row.default_vernacular_name


# Species editor
#
class SpeciesEditor(TreeViewEditorDialog):
    
    visible_columns_pref = "editor.species.columns"
    column_width_pref = "editor.species.column_width"
    default_visible_list = ['genus', 'sp']
    
    label = 'Species'
    
    def __init__(self, parent=None, select=None, defaults={}):  
        TreeViewEditorDialog.__init__(self, tables["Species"],
                                      "Species Editor", parent,
                                      select=select, defaults=defaults)
        titles = {"genusID": "Genus",
                   "sp": "Species",
                   "sp_hybrid": "Sp. hybrid",
                   "sp_qual": "Sp. qualifier",
                   "sp_author": "Sp. author",
                   "cv_group": "Cv. group",
#                   "cv": "Cultivar",
#                   "trades": "Trade name",
#                   "supfam": 'Super family',
#                   'subgen': 'Subgenus',
#                   'subgen_rank': 'Subgeneric rank',
                   'isp': 'Isp. epithet',
                   'isp_rank': 'Isp. rank',
                   'isp_author': 'Isp. author',
#                   'iucn23': 'IUCN 2.3\nCategory',
#                   'iucn31': 'IUCN 3.1\nCategory',
                   'id_qual': 'ID qualifier',
#                   'distribution': 'Distribution'
                    'species_meta': 'Meta Info',
                    'notes': 'Notes',
#                    'default_vernacular_nameID': 'Vernacular Names',
                    'synonyms': 'Synonyms',
                    'vernacular_names': 'Vernacular Names',
				   }

        # make a custom distribution column
#        self.columns.pop('distribution') # this probably isn't necessary     
#        dist_column = ComboColumn(self.view, 'Distribution',
#                           so_col = Species.sqlmeta.columns['distribution'])
#        dist_column.model = self.make_model()
#        self.columns['distribution'] = dist_column                    
        #self.columns['species_meta'] = \
        #    TextColumn(self.view, 'Species Meta', so_col=Species.sqlmeta.joins['species_meta'])
        #self.columns['default_vernacular_nameID'] = \
        
        self.columns.pop('default_vernacular_nameID')
        self.columns['vernacular_names'].meta.editor = \
            editors['VernacularNameEditor']
#        self.columns['vernacular_names'].meta.getter = _get_vernacular_name
        
            #VernacularNameColumn(self, 'Vern name', 
            #                     so_col=Species.sqlmeta.columns['default_vernacular_nameID'])
		#	so_col=Species.sqlmeta.columns['default_vernacular_nameID'])
        #self.columns['default_vernacular_nameID'].meta.editor = \
        #    editors['VernacularNameEditor']
        self.columns['species_meta'].meta.editor = editors["SpeciesMetaEditor"]
        self.columns.titles = titles            
                     
        # should be able to just do a combo list  for the 
        # default_vernacular_name built from the list of vernacular names
                     
        # set completions
        self.columns["genusID"].meta.get_completions= self.get_genus_completions
        self.columns['synonyms'].meta.editor = editors["SpeciesSynonymEditor"]
    
        
    def commit_changes_NO(self):
        # TODO: speciess are a complex typle where more than one field
        # make the plant unique, write a custom commit_changes to get the value
        # from the table as a dictionary, convert this dictionary to 
        # an object that can be accessed by attributes so it mimic a 
        # Species object, pass the dict to species2str and test
        # that a species with the same name doesn't already exist in the 
        # database, if it does exist then ask the use what they want to do
        #super(SpeciesEditor, self).commit_changes()
        values = self.get_values_from_view()
    
          
    def pre_commit_hook(self, values):    
        # need to test each of the values that make up the species
        # against the database, not just the string, i guess we need to
        # check each of the keys in values, check if they are name components
        # use each of these values in a query to speciess
        if values.has_key('id'):
            return True
        exists = False
        select_values = {}
#        debug(values)
        select_values['genusID'] = values['genusID'].id
        select_values['sp'] = values['sp']        
        sel = Species.selectBy(**select_values)
        names = ""
        for s in sel:
            exists = True
            names += "%d: %s\n" % (s.id, s)
        msg  = "The following plant names are similiar to the plant name you "\
               "are trying to create. Are your sure this is what you want to "\
               "do?\n\n" + names
        if exists and not utils.yes_no_dialog(msg):
            return False
        return True
            

    # 
    def get_genus_completions(self, text):
        model = gtk.ListStore(str, object)
        sr = tables["Genus"].select("genus LIKE '"+text+"%'")        
        for row in sr: 
            model.append([str(row), row])
        return model
                
    
    def on_genus_completion_match_selected(self, completion, model, 
                                           iter, path):
        """
        all foreign keys should use entry completion so you can't type in
        values that don't already exists in the database, therefore, allthough
        i don't like it the view.model.row is set here for foreign key columns
        and in self.on_renderer_edited for other column types                
        """        
        genus = model.get_value(iter, 1)
        self.set_view_model_value(path, "genusID", genus)        
        
                                    
#    def make_model(self):
#        model = gtk.TreeStore(str)
#        model.append(None, ["Cultivated"])
#        for continent in tables['Continent'].select(orderBy='continent'):
#            p1 = model.append(None, [str(continent)])
#            for region in continent.regions:
#                p2 = model.append(p1, [str(region)])
#                for country in region.botanical_countries:
#                    p3 = model.append(p2, [str(country)])
#                    for unit in country.units:
#                        if str(unit) != str(country):
#                            model.append(p3, [str(unit)])    
#        return model
                            
      
    def foreign_does_not_exist(self, name, value):
        self.add_genus(value)    


    def add_genus(self, name):
        msg = "The Genus %s does not exist. Would you like to add it?" % name
        if utils.yes_no_dialog(msg):
            print "add genus"

        

# 
# SpeciesSynonymEditor
#
class SpeciesSynonymEditor(TreeViewEditorDialog):

    visible_columns_pref = "editor.species_syn.columns"
    column_width_pref = "editor.species_syn.column_width"
    default_visible_list = ['synonym']
    
    standalone = False
    label = 'Species Synonym'
    
    def __init__(self, parent=None, select=None, defaults={}, connection=None):        
        TreeViewEditorDialog.__init__(self, tables["SpeciesSynonym"], \
                                      "Species Synonym Editor", 
                                      parent, select=select, 
                                      defaults=defaults, connection=connection)
        titles = {'synonymID': 'Synonym of Species'}
                  
        # can't be edited as a standalone so the species should only be set by
        # the parent editor
        self.columns.pop('speciesID')
        
        self.columns.titles = titles
        self.columns["synonymID"].meta.get_completions = \
            self.get_species_completions


    def get_species_completions(self, text):
        # get entry and determine from what has been input which
        # field is currently being edited and give completion
        # if this return None then the entry will never search for completions
        # TODO: finish this, it would be good if we could just stick
        # the table row in the model and tell the renderer how to get the
        # string to match on, though maybe not as fast, and then to get
        # the value we would only have to do a row.id instead of storing
        # these tuples in the model
        # UPDATE: the only problem with sticking the table row in the column
        # is how many queries would it take to screw in a lightbulb, this
        # would be easy to test it just needs to be done
        # TODO: there should be a better/faster way to do this 
        # using a join or something
        parts = text.split(" ")
        genus = parts[0]
        sr = tables["Genus"].select("genus LIKE '"+genus+"%'",
                                    connection=self.transaction)
        model = gtk.ListStore(str, object) 
        for row in sr:
            debug(str(row))
            for species in row.species:                
                model.append((str(species), species))
        return model
    
    
    
try:
    from bauble.plugins.searchview.infobox import InfoBox, InfoExpander, \
        set_widget_value
except ImportError:
    pass
else:
    
#    
# Species infobox for SearchView
#
    class GeneralSpeciesExpander(InfoExpander):
        """
        generic information about an accession like
        number of clones, provenance type, wild provenance type, speciess
        """
    
        def __init__(self, glade_xml):
            InfoExpander.__init__(self, "General", glade_xml)
            w = self.glade_xml.get_widget('general_box')
            w.unparent()
            self.vbox.pack_start(w)
        
        
        def update(self, row):
            set_widget_value(self.glade_xml, 'name_data', 
                             Species.str(row, True, True))
            set_widget_value(self.glade_xml, 'nacc_data', len(row.accessions))
            
            nplants = 0
            for acc in row.accessions:
                nplants += len(acc.plants)
            set_widget_value(self.glade_xml, 'nplants_data', nplants)    
    
    
    class SpeciesInfoBox(InfoBox):
        """
        - general info, fullname, common name, num of accessions and clones
        - reference
        - images
        - redlist status
        - poisonous to humans
        - poisonous to animals
        - food plant
        - origin/distrobution
        """
        def __init__(self):
            """ 
            fullname, synonyms, ...
            """
            InfoBox.__init__(self)
            path = os.path.join(paths.lib_dir(), "plugins", "plants")
            self.glade_xml = gtk.glade.XML(path + os.sep + "species_infobox.glade")
            
            self.general = GeneralSpeciesExpander(self.glade_xml)
            self.add_expander(self.general)
            
            #self.ref = ReferenceExpander()
            #self.ref.set_expanded(True)
            #self.add_expander(self.ref)
            
            #img = ImagesExpander()
            #img.set_expanded(True)
            #self.add_expander(img)
            
            
        def update(self, row):
            self.general.update(row)
            #self.ref.update(row.references)
            #self.ref.value = row.references
            #ref = self.get_expander("References")
            #ref.set_values(row.references)
        
