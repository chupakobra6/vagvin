from django import forms
import re
from typing import Dict, Any, Optional


class VehicleCheckBaseForm(forms.Form):
    """Base form for vehicle check forms"""
    
    def clean_vin(self) -> str:
        """Validate and normalize VIN."""
        vin = self.cleaned_data.get('vin', '').replace(' ', '').strip().upper()
        
        if not vin or len(vin) != 17:
            raise forms.ValidationError("Пожалуйста, введите корректный VIN (17 символов)")
        
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
            raise forms.ValidationError("VIN содержит недопустимые символы")
            
        return vin


class AutotekaCheckForm(forms.Form):
    """Form for Autoteka check."""
    
    vin_input = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите VIN, госномер или ссылку',
            'class': 'form-control check-input'
        })
    )


class CarfaxCheckForm(VehicleCheckBaseForm):
    """Form for Carfax/Autocheck check."""
    
    vin = forms.CharField(
        max_length=17, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите VIN',
            'class': 'form-control check-input'
        })
    )


class VinhistoryCheckForm(VehicleCheckBaseForm):
    """Form for Vinhistory check."""
    
    vin = forms.CharField(
        max_length=17, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите VIN',
            'class': 'form-control check-input'
        })
    )


class AuctionCheckForm(VehicleCheckBaseForm):
    """Form for Auction check."""
    
    vin = forms.CharField(
        max_length=17, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите VIN',
            'class': 'form-control check-input'
        })
    )


class VehicleCheckForm(forms.Form):
    """Form for validating vehicle check requests with multiple input options."""
    
    vin = forms.CharField(
        max_length=17, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Введите VIN (17 символов)'})
    )
    
    regNumber = forms.CharField(
        max_length=12, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Введите регистрационный номер'})
    )
    
    avitoUrl = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'placeholder': 'Введите ссылку на объявление Avito'})
    )
    
    def clean(self) -> Dict[str, Any]:
        """
        Validate that at least one field is provided and validate each field's format.
        
        Returns:
            Dict[str, Any]: Cleaned form data
        """
        cleaned_data = super().clean()
        vin = cleaned_data.get('vin')
        reg_number = cleaned_data.get('regNumber')
        avito_url = cleaned_data.get('avitoUrl')
        
        if not any([vin, reg_number, avito_url]):
            raise forms.ValidationError(
                "Необходимо заполнить хотя бы одно поле: VIN, регистрационный номер или ссылку на Avito."
            )
        
        # Validate VIN if provided
        if vin:
            vin = vin.upper()
            if len(vin) != 17:
                self.add_error('vin', "VIN должен состоять из 17 символов.")
            elif not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):  # VIN standard excludes I, O, Q
                self.add_error('vin', "VIN содержит недопустимые символы.")
        
        # Validate registration number if provided
        if reg_number:
            # Russian reg number regex (e.g., А123БВ77, А123БВ777)
            if not re.match(r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$', reg_number.upper()):
                self.add_error('regNumber', "Неверный формат регистрационного номера.")
        
        # Validate Avito URL if provided
        if avito_url and 'avito.ru' not in avito_url:
            self.add_error('avitoUrl', "URL должен быть ссылкой на объявление Avito.")
        
        return cleaned_data 