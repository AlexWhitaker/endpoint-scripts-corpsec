from helpers.cacheable_api_handler import CacheableApiHandler
from falconpy import IOC, Hosts
import logging


class Crowdstrike(CacheableApiHandler):
    def __init__(self, api_key, allow_local=False, rate_limiters: dict = None, logger= None):
        self.api_base = "https://api.us-2.crowdstrike.com"

        if ":" not in api_key:
            raise Exception("Crowdstrike API key must be in the format 'client_id:client_secret'")
        self.client_id, self.client_secret = api_key.split(":")

        super().__init__(api_key, allow_local, rate_limiters, logger)

    def get_devices_for_domain(self, domain: str, use_cache: bool = True) -> dict:
        if use_cache:
            response = self._get_from_cache("devices_ran_on_legacy", domain)
            if response:
                return response

        self.logger.info(f"[Crowdstrike] API IOC.devices_ran_on_legacy: {domain}")
        falcon_ioc = self._get_ioc_object()

        resource_list = []
        limit = 25
        offset = 0
        while True:
            devices = falcon_ioc.devices_ran_on_legacy(type="domain", value=domain, limit=limit, offset=offset)
            if "error" in devices:
                return resource_list

            resource_list.extend(devices["body"]["resources"])
            if len(devices["body"]["resources"]) < limit:
                break

            offset += limit

        # always add latest data to cache
        self._add_to_cache("devices_ran_on_legacy", domain, resource_list)
        return resource_list

    def get_device_details(self, device_ids: list, use_cache: bool = True) -> dict:
        device_details = []
        if use_cache:
            for device_id in device_ids:
                response = self._get_from_cache("GetDeviceDetails", device_id)
                if response:
                    device_details.append(response)
                    device_ids.remove(device_id)

        if len(device_ids) == 0:
            return device_details

        self.logger.info(f"[Crowdstrike] API Hosts.GetDeviceDetails: {device_ids}")
        falcon_hosts = self._get_hosts_object()
        devices = falcon_hosts.GetDeviceDetails(ids=device_ids)
        if "error" in devices:
            return devices

        for device in devices["body"]["resources"]:
            device_details.append(device)

            # always add latest data to cache
            device_id = device["device_id"]
            self._add_to_cache("GetDeviceDetails", device_id, device)

        return device_details

    def get_processes_ran_on_device(self, device_id: str, domain: str, use_cache: bool = True) -> dict:
        if use_cache:
            response = self._get_from_cache("processes_ran_on_legacy:entities_processes", f"{device_id}:{domain}")
            if response:
                return response

        self.logger.info(f"[Crowdstrike] API IOC.processes_ran_on_legacy: {device_id}, {domain}")
        falcon_ioc = self._get_ioc_object()
        process_ids = falcon_ioc.processes_ran_on_legacy(
            type="domain", value=domain, device_id=device_id, limit=10, offset=0
        )
        if "error" in process_ids:
            return process_ids

        self.logger.info(f"[Crowdstrike] API IOC.entities_processes: {process_ids['body']['resources']}")
        process_info = falcon_ioc.entities_processes(ids=process_ids["body"]["resources"])
        if "error" in process_info:
            return process_info

        # always add latest data to cache
        resource_list = process_info["body"]["resources"]
        self._add_to_cache(
            "processes_ran_on_legacy:entities_processes",
            f"{device_id}:{domain}",
            resource_list,
        )
        return resource_list

    def get_device_and_process_info_for_domain(self, domain: str, use_cache: bool = True) -> dict:
        if use_cache:
            response = self._get_from_cache("device-and-process-info", domain)
            if response:
                return response

        info_for_domain = []
        device_ids = self.get_devices_for_domain(domain, use_cache)
        hosts_details = self.get_device_details(device_ids, use_cache)
        for device_id in device_ids:
            device_info = {"device_id": device_id}

            # get the device details from `hosts_details` by finding the matching device_id
            host_details = next((x for x in hosts_details if x["device_id"] == device_id), None)
            if host_details is not None:
                device_info["device_details"] = {
                    "hostname": host_details["hostname"],
                    "platform": host_details["platform_name"],
                    "os_version": host_details["os_version"],
                    "last_login_user": host_details["last_login_user"],
                    "serial_number": host_details["serial_number"],
                }
            else:
                device_info["device_details"] = None

            processes = []
            for process in self.get_processes_ran_on_device(device_id, domain, use_cache):
                processes.append(
                    {
                        "process_id": process["process_id"],
                        "file_name": process["file_name"],
                        "command_line": process["command_line"],
                        "start_timestamp": process["start_timestamp"],
                        "stop_timestamp": process["stop_timestamp"],
                    }
                )
            device_info["processes"] = processes

            info_for_domain.append(device_info)

        if use_cache:
            self._add_to_cache("device-and-process-info", domain, info_for_domain)

        return info_for_domain

    def _get_from_cache(self, api_method: str, url: str) -> dict:
        return super().get_from_cache(f"{api_method}:{url}")

    def _add_to_cache(self, api_method: str, url: str, data: dict):
        super().add_to_cache(f"{api_method}:{url}", None, data)

    def _get_ioc_object(self):
        if not hasattr(self, "ioc"):
            self.ioc = IOC(client_id=self.client_id, client_secret=self.client_secret)
        return self.ioc

    def _get_hosts_object(self):
        if not hasattr(self, "hosts"):
            self.hosts = Hosts(client_id=self.client_id, client_secret=self.client_secret)
        return self.hosts
