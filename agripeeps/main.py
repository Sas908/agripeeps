#start 
#Main class
from typing import Optional
from pydantic import BaseModel
import pandas as pd
from datetime import date
import logging
import itertools
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from sentier_data_tools import (
    DatasetKind,
    Dataset,
    Demand,
    Flow,
    FlowIRI,
    GeonamesIRI,
    ModelTermIRI,
    ProductIRI,
    SentierModel,
)

from sentier_data_tools.iri import VocabIRI
import DirectFertiliserEmission as dfe

## Attention : I would like demand to come from user input, I need mapping from natural language to IRI for product and geonames

class UserInput(BaseModel):
    product_iri: ProductIRI
    unit : ProductIRI
    #properties: Optional[list]
    amount: float
    climate_type : Optional[str] = None
    crop_yield : Optional[float] = None
    fertilizer_amount : Optional[float] = None
    spatial_context: GeonamesIRI = GeonamesIRI("https://sws.geonames.org/2782113")
    begin_date: Optional[date] = None
    end_date: Optional[date] = None
    
    class Config:
        arbitrary_types_allowed = True

class RunConfig(BaseModel):
    num_samples: int = 1000

class Crop(SentierModel):
    def __init__(self, user_input: UserInput, run_config: RunConfig):
        self.aliases = {ProductIRI(
            "http://data.europa.eu/xsp/cn2024/100500000080"
            ): "corn",
            ProductIRI(
            "http://data.europa.eu/xsp/cn2024/060011000090"
            ): "crop",
            ProductIRI(
            "http://data.europa.eu/xsp/cn2024/310200000080"
            ): "mineral_fertiliser",
            ProductIRI(
            "https://vocab.sentier.dev/model-terms/crop_yield"
            ): "crop_yield"}
        # Assuming user_input maps to demand in SentierModel
        super().__init__(demand=user_input, run_config=run_config)

    def get_master_db(self) -> None :
        logging.info(self.crop)
        agridata_bom = self.get_model_data(
            product=self.corn, kind=DatasetKind.BOM #, location=self.demand.spatial_context
        )
        logging.info(agridata_bom)
        for i in agridata_bom["exactMatch"]:
            #print(self.mineral_fertiliser)
            if self.mineral_fertiliser in [ProductIRI(col["iri"]) for col in i.columns]:
                self.mineral_fertiliser_data = i.dataframe
                logging.info(f"Set input data: {i.name}")

        # agridata_param = self.get_model_data(
        #     product=self.crop, kind=DatasetKind.PARAMETERS
        # )
        # for i in agridata_param["exactMatch"]:
        #     if self.crop_yield in [ProductIRI(col["iri"]) for col in i.columns]:
        #         self.crop_yield_data = i.dataframe
        #         logging.info(f"Set input data: {self.crop_yield}")
                
        #self.masterDB = pd.read_csv('../docs/MasterDB.csv')
        logging.info("Getting master db")
        
        return agridata_bom
        
    def get_all_input(self) -> float :
        
        if self.demand.climate_type is None:
            self.climate_key = 'default'
        else:
            # Ensure wet_climate is either 'wet' or 'dry'
            if self.demand.climate_type not in ['wet', 'dry']:
                logging.error(f"Invalid climate type value: {self.demand.climate_type}. Expected 'wet', 'dry', or None.")
            self.climate_key = self.demand.climate_type
            
        if self.demand.crop_yield is None :
            self.demand.crop_yield = 7.0 #to be modified as a function of self.masterDB
        if self.demand.fertilizer_amount is None :
            self.demand.fertilizer_amount = 70 #To be modified as a function of self.masterDB
        logging.info("Getting crop yield and fertilizer amount")
        
    def get_emissions(self) :
        self.fertilizer_n_per_ha = dfe.run(self.demand.product_iri, self.demand.fertilizer_amount, self.climate_key)
        logging.info("Getting emission from fertilizer")
        
    def run(self):
        self.get_master_db()
        self.get_all_input()
        self.get_emissions()

    # def get_model_data(
    #     self,
    #     product: VocabIRI,
    #     kind: DatasetKind,
    #     location: GeonamesIRI = None
    # ) -> dict:
    #     logging.log(logging.INFO, f"{location}")
    #     results = {
    #         "exactMatch": list(
    #             Dataset.select().where(
    #                 Dataset.kind == kind,
    #                 Dataset.product == str(product),
    #                 Dataset.location == location
    #             )
    #         ),
    #         "broader": list(
    #             Dataset.select().where(
    #                 Dataset.kind == kind,
    #                 Dataset.product << product.broader(raw_strings=True),
    #                 Dataset.location == GeonamesIRI(location)
    #             )
    #         ),
    #         "narrower": list(
    #             Dataset.select().where(
    #                 Dataset.kind == kind,
    #                 Dataset.product << product.narrower(raw_strings=True),
    #                 Dataset.location == GeonamesIRI(location)
    #             )
    #         ),
    #     }
    #     for df in itertools.chain(*results.values()):
    #         df.dataframe.apply_aliases(self.aliases)

    #     return results
