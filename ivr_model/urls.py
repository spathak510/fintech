from django.urls import path, include
from ivr_model import views as ivr_model_views

urlpatterns = [
    path('ivr-calling/',ivr_model_views.IVRCalling.as_view()),
    path('temp', ivr_model_views.index, name='index'),
    
    path('select-language/<int:cid>', ivr_model_views.create_language_selection_twiml, name='select_language'),
    path('handle-language-selection/<int:cid>', ivr_model_views.handle_language_selection, name='handle_language_selection'),
    path('handle-input-english/<int:cid>', ivr_model_views.handle_input_english, name='handle_input_english'),
    path('handle-input-hindi/<int:cid>', ivr_model_views.handle_input_hindi, name='handle_input_hindi'),
]