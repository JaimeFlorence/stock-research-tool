from config_manager import ConfigManager

class IntrinsicValueCalculator:
    """A class to compute intrinsic value of stocks using DCF, PEG, and hybrid methods."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize with a ConfigManager instance."""
        self.config_manager = config_manager
    
    def calculate_dcf(self, fcf, growth_rate, discount_rate, years=10, terminal_growth=0.02):
        """
        Calculate total DCF value based on free cash flow projections.
        
        Args:
            fcf (float): Free cash flow.
            growth_rate (float): Annual growth rate (decimal).
            discount_rate (float): Discount rate (decimal).
            years (int): Number of projection years.
            terminal_growth (float): Terminal growth rate (decimal).
            
        Returns:
            float: Total DCF value for the company.
        """
        future_cash_flows = [fcf * (1 + growth_rate) ** t for t in range(1, years + 1)]
        terminal_value = (future_cash_flows[-1] * (1 + terminal_growth) / 
                         (discount_rate - terminal_growth))
        discounted_cf = [cf / (1 + discount_rate) ** t for t, cf in enumerate(future_cash_flows, 1)]
        dcf_value = sum(discounted_cf) + terminal_value / (1 + discount_rate) ** years
        return dcf_value
    
    def get_intrinsic_value(self, stock_data):
        """
        Compute intrinsic value per share using DCF, PEG, and FMP DCF.
        
        Args:
            stock_data (dict): Stock data with keys like 'price', 'shares', 'fcf', 'eps', 
                              'sector', 'growth_rate', 'fmp_dcf'.
                              
        Returns:
            float or None: Intrinsic value per share, or None if no values are calculable.
        """
        sector = stock_data['sector']
        sector_defaults = self.config_manager.get_sector_params(sector)
        
        price = stock_data['price']
        shares = stock_data['shares']
        fcf = stock_data.get('fcf')
        eps = stock_data.get('eps')
        growth_rate = stock_data.get('growth_rate', sector_defaults.get('growth_rate', 0.05))
        discount_rate = sector_defaults.get('discount_rate', 0.10)
        sector_pe = sector_defaults.get('pe_ratio', 15.0)
        fmp_dcf = stock_data.get('fmp_dcf')
        
        # DCF intrinsic value per share
        dcf_per_share = None
        if fcf and shares > 0:
            dcf_total = self.calculate_dcf(fcf, growth_rate, discount_rate)
            dcf_per_share = dcf_total / shares
        
        # PEG-based intrinsic value per share
        peg_intrinsic = None
        if eps and eps > 0 and growth_rate > 0:
            sector_growth = sector_defaults.get('growth_rate', growth_rate)
            fair_pe = sector_pe * (growth_rate / sector_growth) if sector_growth > 0 else sector_pe
            peg_intrinsic = fair_pe * eps
        
        # Combine available values into hybrid valuation
        values = [v for v in [dcf_per_share, peg_intrinsic, fmp_dcf] if v is not None]
        return sum(values) / len(values) if values else None