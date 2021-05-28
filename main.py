from utils.scraper import ImmoWebScraper
import time

if __name__ == "__main__":
    start = time.perf_counter()

    immoWeb = ImmoWebScraper()
    immoWeb.get_urls()
    print(f'Recorded {len(immoWeb.data_list)} urls in {time.perf_counter() - start:.4f} seconds')
    
    immoWeb.scrap_data()
    print(f'Scrapped all data in {time.perf_counter() - start:.4f} seconds')
    
    immoWeb.fill_dataframe()
    immoWeb.df.to_csv(r'./houses_to_sale.csv')

    print(f'Filled & saved dataframe of {len(immoWeb.data_list)} items in {time.perf_counter() - start:.4f} seconds')
